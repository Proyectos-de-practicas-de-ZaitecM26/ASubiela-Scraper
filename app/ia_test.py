from google import genai

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents="Explain how AI works in a few words"
)
print(response.text)

from google import genai

client = genai.Client()

interaction =  client.interactions.create(
    model="gemini-3-flash-preview",
    input="Tell me a short joke about programming."
)

print(interaction.outputs[-1].text)
