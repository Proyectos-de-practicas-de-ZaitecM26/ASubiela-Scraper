from flask import Blueprint, request, jsonify
from app.services.ai_client import ask_groq

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chatbot/api", methods=["POST"])
def chatbot_api():
    data = request.get_json()
    message = data.get("message", "")

    if not message:
        return jsonify({"reply": "Escribe algo 😊"})

    reply = ask_groq(message)

    return jsonify({"reply": reply})