import os
from groq import Groq

BASE_SYSTEM_PROMPT = """
Eres un asistente experto en el BOE de Espana.
Tu única función es responder dudas sobre leyes y decretos.
Responde en espanol de forma clara, breve y util.
Ayuda con busqueda, filtros, provincias, fechas y lectura de convocatorias.
Si el usuario te pregunta sobre cualquier otro tema (deportes, cocina, fútbol, etc.),
debes responder estrictamente: 'Solo estoy capacitado para hablar sobre el contenido del BOE'
""".strip()


def _build_system_prompt(extra_instructions=None):
    if extra_instructions:
        return f"{BASE_SYSTEM_PROMPT}\n\n{extra_instructions.strip()}"
    return BASE_SYSTEM_PROMPT


def chatbot(user_message, extra_instructions=None):
    api_key = os.getenv("GROK_KEY")
    if not api_key:
        raise ValueError("Falta configurar API Key en el servidor.")

    try:
        client = Groq(api_key=api_key)
        system_prompt = _build_system_prompt(extra_instructions)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=450,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": user_message},
            ],
        )

        return completion.choices[0].message.content or "No tengo respuesta ahora mismo."
    except:
        raise ValueError("El chatbot no está disponible en este momento")