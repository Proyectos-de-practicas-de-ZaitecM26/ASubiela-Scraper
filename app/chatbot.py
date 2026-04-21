# =========================================================
# Refactorización: Desacoplo el chatbot del proveedor de IA
# =========================================================

from app.services.ai_client import ask_ai


BASE_SYSTEM_PROMPT = """
Eres un asistente experto en el BOE de España.
Tu única función es responder dudas sobre leyes y decretos.
Responde en español de forma clara, breve y util.
Ayuda con busqueda, filtros, provincias, fechas y lectura de convocatorias.
Si el usuario te pregunta sobre cualquier otro tema (deportes, cocina, fútbol, etc.),
debes responder estrictamente: 'Solo estoy capacitado para hablar sobre el contenido del BOE'
""".strip()


# =========================================================
# Construyo el prompt base con posibles instrucciones extra
# =========================================================
def _build_system_prompt(extra_instructions=None):
    if extra_instructions:
        return f"{BASE_SYSTEM_PROMPT}\n\n{extra_instructions.strip()}"
    return BASE_SYSTEM_PROMPT


# =========================================================
# Función principal del chatbot
# =========================================================
def chatbot(user_message, extra_instructions=None):
    system_prompt = _build_system_prompt(extra_instructions)

    try:
        response = ask_ai(
            message=user_message,
            provider="groq",  
            system_prompt=system_prompt
        )

        return response or "No tengo respuesta ahora mismo."

    except Exception:
        raise ValueError("El chatbot no está disponible en este momento")