import { exec } from 'child_process';
import cors from 'cors';
import dotenv from 'dotenv';
import express from 'express';
import { promises as fs } from 'fs';
import Groq from 'groq-sdk';
import ffmpeg from 'ffmpeg-static';

// Check current directory first, then fallback to the root Haven-main directory
dotenv.config(); 
dotenv.config({ path: '../../.env' });

const PYTHON_PATH = '"G:\\Haven-main\\.venv\\Scripts\\python.exe"';

const groq = new Groq({
  apiKey: (process.env.GROQ_API_KEY || 'missing_api_key').trim(),
});

const voiceID = 'en-IN-NeerjaNeural';

const app = express();
app.use(express.json());
app.use(cors());
const port = process.env.PORT || 3001;

let conversationHistory = []; // Stores the chat history for memory

app.get('/', (req, res) => {
  res.send('Hello World!');
});

app.get('/voices', async (req, res) => {
  res.send([{ voice_id: voiceID, name: "Christopher (Free Neural)" }]);
});


const execCommand = (command) => {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) reject(error);
      resolve(stdout);
    });
  });
};

const lipSyncMessage = async (message) => {
  const time = new Date().getTime();
  console.log(`Starting conversion for message ${message}`);
  await execCommand(
    `"${ffmpeg}" -y -i audios/message_${message}.mp3 audios/message_${message}.wav`
    // -y to overwrite the file
  );
  console.log(`Conversion done in ${new Date().getTime() - time}ms`);
  await execCommand(
    `"G:\\Haven-main\\rhubarb\\Rhubarb-Lip-Sync-1.13.0-Windows\\rhubarb.exe" -f json -o audios/message_${message}.json audios/message_${message}.wav -r phonetic`
  );
  // -r phonetic is faster but less accurate
  console.log(`Lip sync done in ${new Date().getTime() - time}ms`);
};

app.post('/chat', async (req, res) => {
  const userMessage = req.body.message;
  console.log(`\n--- New Chat Request ---`);
  console.log(`Message received: "${userMessage || 'Empty (Loading Intro)'}"`);

  if (!userMessage) {
    conversationHistory = []; // Reset memory when the page is refreshed
    try {
    res.send({
      messages: [
        {
          text: 'Hello, I am your virtual therapist. How are you feeling today?',
          audio: await audioFileToBase64('audios/intro_0.wav'),
          lipsync: await readJsonTranscript('audios/intro_0.json'),
          facialExpression: 'smile',
          animation: 'Talking_1',
        },
        {
          text: "I am here to listen and support you. You are in a safe space.",
          audio: await audioFileToBase64('audios/intro_1.wav'),
          lipsync: await readJsonTranscript('audios/intro_1.json'),
          facialExpression: 'calm',
          animation: 'Idle',
        },
      ],
    });
    } catch (err) {
      console.error('Error loading intro audio/json:', err);
      res.status(500).send({ error: 'Failed to load intro' });
    }
    return;
  }

  if (!process.env.GROQ_API_KEY) {
    console.error('GROQ_API_KEY environment variable not set.');
    res.status(500).send({
      error: 'Server configuration error: The GROQ_API_KEY environment variable is not set in your .env file.',
    });
    return;
  }

  const systemPrompt = `You are a virtual therapy bot designed to provide emotional support and advice to women. Your goal is to listen empathetically, offer thoughtful advice, and remember details from previous messages in the conversation.
Respond with a JSON object containing a "messages" array (max 3). Each message should include the following properties:
- text: The message you are sending to the user.
- facialExpression: The emotional tone. STRICTLY choose from: smile, sad, angry, surprised, funnyFace, default.
- animation: The body animation. STRICTLY choose from: Talking_0, Talking_1, Talking_2, Crying, Laughing, Angry, Idle.

You output strictly valid JSON objects.`;

  // Add user's message to the memory
  conversationHistory.push({ role: 'user', content: userMessage });
  
  // Keep the history manageable (last 20 messages) to prevent token limits
  if (conversationHistory.length > 20) {
    conversationHistory = conversationHistory.slice(conversationHistory.length - 20);
  }

  let messages = [];
  try {
    const completion = await groq.chat.completions.create({
      messages: [
        { role: 'system', content: systemPrompt },
        ...conversationHistory
      ],
      model: 'llama3-8b-8192',
      model: 'llama-3.1-8b-instant',
      temperature: 0.5,
      response_format: { type: 'json_object' }
    });
    const resultText = completion.choices[0]?.message?.content || '{"messages": []}';
    const parsed = JSON.parse(resultText);
    messages = parsed.messages || parsed || [];
    console.log('Parsed JSON response:', messages);

    // Save the AI's EXACT JSON response back into memory so it doesn't break Groq's JSON mode
    conversationHistory.push({ role: 'assistant', content: resultText });
  } catch (error) {
    console.error('Error with Groq API:', error);
    res
      .status(500)
      .send({ error: 'Error generating response from AI.' });
    return;
  }
  try {
    for (let i = 0; i < messages.length; i++) {
      const message = messages[i];
      // Ensure audios folder exists so saving the file doesn't crash
      await fs.mkdir('audios', { recursive: true }).catch(() => {});
      // generate audio file
      const fileName = `audios/message_${i}.mp3`; // The name of your audio file
      
      // Save text to a temporary file to avoid shell quoting errors
      const textFile = `audios/message_${i}.txt`;
      await fs.writeFile(textFile, message.text);
      
      // Generate free audio using edge-tts
      console.log(`Generating audio for message ${i} using edge-tts...`);
      await execCommand(`${PYTHON_PATH} -m edge_tts --voice "${voiceID}" -f ${textFile} --write-media ${fileName}`);

      // generate lipsync
      await lipSyncMessage(i);
      message.audio = await audioFileToBase64(`audios/message_${i}.wav`);
      message.lipsync = await readJsonTranscript(`audios/message_${i}.json`);
      
      // Cleanup text file
      await fs.unlink(textFile).catch(e => console.error(e));
    }
  } catch (error) {
    console.error('Error generating Audio/LipSync:', error);
    res.status(500).send({ error: `Audio Generation Failed: ${error.message}` });
    return;
  }

  res.send({ messages });
});

const readJsonTranscript = async (file) => {
  const data = await fs.readFile(file, 'utf8');
  return JSON.parse(data);
};

const audioFileToBase64 = async (file) => {
  const data = await fs.readFile(file);
  return data.toString('base64');
};

app.listen(port, "0.0.0.0", () => {
  console.log(`Virtual Girlfriend listening on port ${port}`);
});
