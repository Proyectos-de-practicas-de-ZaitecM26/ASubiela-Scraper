from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from app.extensions import limiter
from ..services.chatbot import chatbot

chat_bp = Blueprint("chatbot", __name__)

@chat_bp.route("/api/chatbot", methods=["POST"])
@limiter.limit("20 per minute")
def chatbot_api():

    payload = request.get_json(silent=True) or {}

    user_message = (
        payload.get("message") or ""
    ).strip()

    if not user_message:

        return jsonify({
            "ok": False,
            "error": "Mensaje vacío."
        }), 400

    if len(user_message) > 1200:

        return jsonify({
            "ok": False,
            "error": "Mensaje demasiado largo."
        }), 400

    try:

        answer = chatbot(user_message)

        return jsonify({
            "ok": True,
            "answer": answer
        })

    except ValueError as exc:

        current_app.logger.exception(
            "Error en /api/chatbot: %s",
            exc
        )

        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500

    except Exception as exc:

        current_app.logger.exception(
            "Error en /api/chatbot: %s",
            exc
        )

        return jsonify({
            "ok": False,
            "error": "No se pudo generar respuesta."
        }), 500