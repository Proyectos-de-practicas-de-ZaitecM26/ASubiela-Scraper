import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv(override=True)

api_key = os.getenv("GROQ_API_KEY")


if not api_key:
    raise ValueError("No GROQ_API_KEY")

client = Groq(api_key=api_key)


def ask_groq(message):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Eres un asistente del BOE."},
            {"role": "user", "content": message}
        ],
    )
    return response.choices[0].message.content