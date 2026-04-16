import os
from groq import Groq

def chatbot (user_message):
    api_key = os.getenv("GROK_KEY")
    if not api_key:
        raise ValueError("Falta configurar API Key en el servidor.")

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=450,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente para una web de oposiciones del BOE en Espana. "
                        "Responde en espanol de forma clara, breve y util. "
                        "Ayuda con busqueda, filtros, provincias, fechas y lectura de convocatorias."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
        )

        return completion.choices[0].message.content or "No tengo respuesta ahora mismo."
    except:
        raise ValueError ("El chatbot no está disponible en este momento")