import os

from groq import Groq


client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "How does AI work?"},
    ],
)

print(response.choices[0].message.content)