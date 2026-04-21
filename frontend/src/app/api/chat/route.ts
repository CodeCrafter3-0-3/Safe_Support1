import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { userInput } = await req.json();

    if (!userInput) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    if (!process.env.GROQ_API_KEY) {
      console.error("CRITICAL ERROR: GROQ_API_KEY is missing from environment variables!");
      return NextResponse.json({ error: 'Missing API Key' }, { status: 500 });
    }

    const prompt = `You are an expert legal advisor and supportive assistant specializing in Indian Law, Women's Rights, and Women's Empowerment.
Provide accurate, empathetic, and clear advice or content based on the user's query. If the user asks for a poem or general empowerment content, provide that as well.
Format your response cleanly using Markdown for readability.

User Query:
"""
${userInput}
"""`;

    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GROQ_API_KEY.trim()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: [
          { role: 'system', content: 'You are a helpful and empathetic legal assistant.' },
          { role: 'user', content: prompt }
        ],
        temperature: 0.5,
      })
    });

    const data = await response.json();
    if (!response.ok) {
      console.error('Groq API Rejected Request:', data);
      return NextResponse.json({ error: 'Groq API Error' }, { status: 500 });
    }

    const result = data.choices[0]?.message?.content || 'I could not generate a response.';

    return NextResponse.json({ reply: result });
  } catch (error: any) {
    console.error('Groq Chat Exception:', error.message);
    if (error.cause) console.error('Underlying cause:', error.cause);
    return NextResponse.json(
      { error: 'There was an issue processing your request.' },
      { status: 500 }
    );
  }
}
