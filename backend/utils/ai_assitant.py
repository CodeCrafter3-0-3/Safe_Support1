import os
import asyncio

import google.generativeai as genai
import speech_recognition as sr
from dotenv import load_dotenv
import edge_tts
import pygame

# Force load the .env file from the backend directory regardless of where the script is run
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class colors:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"  # End color sequence


class AI_Assistant:
    def __init__(self):
        self.full_transcript = []

    def start_transcription(self):
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()

    def stop_transcription(self):
        pass

    def speech_to_text(self):
        with sr.Microphone() as source:
            print(colors.PURPLE + colors.BOLD + "\n User: " + colors.END)
            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio)
            print(f"{text}")
            self.generate_ai_response(text)
        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Speech Recognition service; {e}")

    def generate_ai_response(self, text):
        self.full_transcript.append({"role": "user", "content": text})
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"You are a helpful, empathetic therapist. Keep your response brief, conversational, and supportive. The user says: {text}"
        ai_response = model.generate_content(prompt)

        print(colors.GREEN + "\nAI Receptionist: " + colors.END)
        print(ai_response.text)
        self.generate_audio(ai_response.text)

    def generate_audio(self, text):
        self.full_transcript.append({"role": "assistant", "content": text})
        
        audio_file = "response.mp3"
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        asyncio.run(communicate.save(audio_file))
        
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        
        if os.path.exists(audio_file):
            os.remove(audio_file)


if __name__ == "__main__":
    print("\n\n\n")
    greeting = "Hey there! How are you feeling today?"
    print(colors.GREEN + "\nAI Receptionist: " + colors.END)
    print(greeting)
    ai_assistant = AI_Assistant()
    ai_assistant.generate_audio(greeting)
    ai_assistant.start_transcription()

    # Continuously listen for speech input
    while True:
        ai_assistant.speech_to_text()
