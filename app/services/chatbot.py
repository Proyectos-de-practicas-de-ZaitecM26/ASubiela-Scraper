import os
from .chat_skills import get_chat_skill_decision
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


def chatbot(user_message):
    api_key = os.getenv("GROK_KEY")
    if not api_key:
        raise KeyError("Falta configurar API Key en el servidor.")

    #decision = get_chat_skill_decision(user_message)

    #if decision.blocked:
       #raise ValueError(decision.block_message)
    
    try:
        client = Groq(api_key=api_key)
        system_prompt = _build_system_prompt()
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