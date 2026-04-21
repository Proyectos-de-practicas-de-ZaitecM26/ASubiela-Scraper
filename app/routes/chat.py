# =========================================================
# Refactorización: separo validación, uso el cliente de IA unificado
# y mejoro el control de errores para que el código sea más limpio
# =========================================================

from flask import Blueprint, request, jsonify
from app.services.ai_client import ask_ai

chat_bp = Blueprint("chat", __name__)


# =========================================================
# Valido el mensaje del usuario para evitar errores y spam
# =========================================================
def validar_mensaje(message):
    if not message or not message.strip():
        return "Escribe algo 😊"

    if len(message) > 500:
        return "Mensaje demasiado largo"

    return None


# =========================================================
# Endpoint principal del chatbot
# =========================================================
@chat_bp.route("/chatbot/api", methods=["POST"])
def chatbot_api():
    try:
        data = request.get_json()
        message = data.get("message", "")

        # Validación separada (más limpio y reutilizable)
        error = validar_mensaje(message)
        if error:
            return jsonify({"reply": error})

        # Uso del cliente centralizado de IA
        reply = ask_ai(
            message=message,
            provider="groq"
        )

        return jsonify({"reply": reply})

    except Exception as e:
        # Evito romper la app y no expongo errores internos
        print(f"[ERROR CHATBOT]: {e}")
        return jsonify({"reply": "Error interno, inténtalo más tarde"})