import os
from groq import Groq
from dotenv import load_dotenv

# Cargamos las variables del archivo .env
load_dotenv()

def obtener_respuesta_groq(mensaje_usuario):
    try:
        client = Groq(
            api_key=os.environ.get("GROQ_KEY"),
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": mensaje_usuario,
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error al conectar con Groq: {str(e)}"