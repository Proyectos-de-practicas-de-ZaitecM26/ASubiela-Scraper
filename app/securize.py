import os
from flask import Flask, render_template, session, request, jsonify
from datetime import timedelta

app = Flask()

# Usamos el nombre de la variable que configuraste en tu entorno
api_key = os.getenv("GROK_KEY")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True, 
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30)
)

@app.route('/')
def index():
    # El servidor marca la sesión como válida al cargar el HTML
    session['api_access'] = True 
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    # Verificación invisible: ¿Tiene la cookie de sesión válida?
    if not session.get('api_access'):
        return jsonify({"error": "No autorizado"}), 403

    # Tu lógica de procesamiento aquí
    user_msg = request.json.get('message')
    return jsonify({"response": f"Respuesta del bot a: {user_msg}"})