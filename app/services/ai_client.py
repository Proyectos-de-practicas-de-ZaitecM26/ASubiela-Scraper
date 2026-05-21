# =========================================================
# Refactorización: Centralizo todas las llamadas a IA en un solo punto
# para evitar duplicación y permitir cambiar de proveedor fácilmente
# =========================================================

import os
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from google import genai
from flask import current_app

# Cargo variables de entorno
load_dotenv(override=True)


# =========================================================
# CLIENTES (se inicializan una vez)
# =========================================================

groq_client = None
openrouter_client = None
gemini_client = None


def _get_groq_client():
    global groq_client
    if groq_client is None:
        api_key = current_app.config.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Falta GROQ_API_KEY")
        groq_client = Groq(api_key=api_key)
    return groq_client


def _get_openrouter_client():
    global openrouter_client
    if openrouter_client is None:
        api_key = current_app.config.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("Falta OPENROUTER_API_KEY")

        openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return openrouter_client

def _get_gemini_client():
    global gemini_client
    if gemini_client is None:
        api_key = current_app.config.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Falta GEMINI_API_KEY")
        gemini_client = genai.Client(api_key=api_key)
    return gemini_client

# =========================================================
# FUNCIONES POR PROVEEDOR
# =========================================================

def ask_groq(message, system_prompt):
    # Uso Groq como proveedor principal
    client = _get_groq_client()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        temperature=0.3,
        max_tokens=400,
    )

    return response.choices[0].message.content


def ask_gemini(message):
    # Alternativa con Gemini
    client = _get_gemini_client()
    chat = client.chats.create(model="gemini-2.5-flash-lite")

    response = chat.send_message(message)
    return response.text


def ask_openrouter(message, model):
    # Unifico Nvidia / Elephant
    client = _get_openrouter_client()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}],
    )

    return response.choices[0].message.content


# =========================================================
# FUNCIÓN PRINCIPAL (LA QUE USA EL CHATBOT)
# =========================================================

def ask_ai(message, system_prompt=None):
    provider = current_app.config.get("DEFAULT_AI_PROVIDER")
    current_app.logger.info(f"Usando proveedor de IA: {provider}")
    
    if provider == "groq":
        return ask_groq(message, system_prompt)

    elif provider == "gemini":
        return ask_gemini(message)

    elif provider == "nvidia":
        return ask_openrouter(message, "nvidia/nemotron-3-nano-30b-a3b:free")

    elif provider == "elephant":
        return ask_openrouter(message, "openrouter/elephant-alpha")

    else:
        raise ValueError("Proveedor de IA no válido")