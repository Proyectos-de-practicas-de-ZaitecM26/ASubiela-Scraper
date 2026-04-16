import os
import sys
from google import genai


def iniciar_chat():
    # Inicializamos el cliente
    client = genai.Client()

    # Iniciamos una sesión de chat con un historial vacío
    chat_session = client.chats.create(model="gemini-2.5-flash-lite")

    print("--- Gemini Terminal Chat (v1.72.0) ---")
    print("Escribe 'salir' o 'exit' para terminar la conversación.\n")

    while True:
        try:
            # Captura de la pregunta del usuario
            user_input = input("➤ Tú: ")

            if user_input.lower() in ["salir", "exit", "quit"]:
                print("\n ¡Hasta luego!")
                break

            if not user_input.strip():
                continue

            # Envío del mensaje y recepción de respuesta
            response = chat_session.send_message(user_input)
            
            # Impresión de la respuesta de Gemini
            print(f"\n Gemini: {response.text}\n")
            print("-" * 40)

        except KeyboardInterrupt:
            print("\n\nInterrupción detectada. Cerrando...")
            sys.exit(0)
        except Exception as e:
            print(f" Error: {e}")

if __name__ == "__main__":
    iniciar_chat()