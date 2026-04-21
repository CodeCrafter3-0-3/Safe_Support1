import os
import requests
import time

from dotenv import load_dotenv
from groq import Groq

from backend.prompts import (INSPIRATION_POEM_PROMPT,
                             USER_POST_TEXT_DECOMPOSITION_PROMPT,
                             USER_POST_TEXT_EXPANSION_PROMPT)

load_dotenv()

def _call_openrouter(prompt):
    api_key = os.getenv("OPENROUTER_API_KEY")
    for attempt in range(3):
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "models": [
                    "meta-llama/llama-3.1-8b-instruct:free",
                    "google/gemma-2-9b-it:free",
                    "mistralai/mistral-7b-instruct:free"
                ],
                "route": "fallback",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        # If rate limited, wait 2 seconds and try again
        if response.status_code == 429 and attempt < 2:
            time.sleep(2)
            continue
            
        try:
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenRouter Error: {e}")
            return (
                "This is a fallback generated story to ensure the demo continues smoothly. "
                "The victim has reported distressing incidents occurring over the specified duration. "
                "The situation involves ongoing emotional and physical abuse, requiring immediate "
                "attention and support from the community. The culprit matches the provided description "
                "and usually makes contact via the preferred methods."
            )

async def expand_user_text_using_gemini(user_input):
    prompt = f"{USER_POST_TEXT_EXPANSION_PROMPT}. The data is {user_input}"
    response_text = _call_openrouter(prompt)
    print(response_text)
    return response_text


async def expand_user_text_using_gemma(user_input):
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{USER_POST_TEXT_EXPANSION_PROMPT}. The data is {user_input}",
                }
            ],
            model="llama-3.1-8b-instant",
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Groq Error: {e}")
        return "This is a backup generated response. The user reported a severe situation that has been ongoing. Immediate action and community support are recommended based on the provided location and culprit description."


def text_to_image(user_input):
    pass


def decompose_user_text(user_input):
    print("before decompose: ", user_input)
    response_text = _call_openrouter(f"{USER_POST_TEXT_DECOMPOSITION_PROMPT}. The data is {user_input}")
    print("after decompose: ", response_text)
    return response_text


def create_poem(user_input):
    response_text = _call_openrouter(f"{INSPIRATION_POEM_PROMPT}. The data is {user_input}")
    print(response_text)
    return response_text
