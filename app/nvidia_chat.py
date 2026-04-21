import os
import sys
from openai import OpenAI


SECRET_KEY = os.getenv("OPENROUTER_API_KEY", "cambia-esto-en-produccion")

def iniciar_chat():
    # Inicializamos el cliente
    client = OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=SECRET_KEY,
      timeout=20.0
    )
    print("--- OpenAI Terminal Chat ---")
    
    conversation=[]

    while True:
        try:
            # Captura de la pregunta del usuario
            user_input = input("Pregunta: ")

            if user_input.lower() in ["salir", "exit", "quit"]:
                print("\n ¡Adiós!")
                break

            if not user_input.strip():
                continue
              
            conversation.append({
                        "role": "user",
                        "content": user_input
                      })

            # Envío del mensaje y recepción de respuesta
            response = client.chat.completions.create(
              model="nvidia/nemotron-3-nano-30b-a3b:free",
              messages=conversation,
              extra_body={"reasoning": {"enabled": True}} #---modo razonamiento activado
            )
            
            conversation.append({
                        "role": "assistant",
                        "content":response.choices[0].message.content
                      })
            
            # Impresión de la respuesta
            print(f"\n nvidia/nemotron: {response.choices[0].message.content}\n")
            print("-" * 40)

        except KeyboardInterrupt:
            print("\n\nInterrupción detectada. Cerrando...")
            sys.exit(0)
        except Exception as e:
            print(f" Error: {e}")

if __name__ == "__main__":
    iniciar_chat()