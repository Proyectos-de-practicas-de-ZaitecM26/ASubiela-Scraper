import os
import time

from google import genai


def get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Set GEMINI_API_KEY (or GOOGLE_API_KEY) before running this script."
        )
    return api_key


def main() -> None:
    client = genai.Client(api_key=get_api_key())
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    prompt = "Explain how AI works in a few words"

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            print(response.text)
            return
        except Exception as exc:
            # Retry only temporary server-side overload errors (e.g., 503 UNAVAILABLE).
            is_server_error = exc.__class__.__name__ == "ServerError"
            is_unavailable = "503" in str(exc) or "UNAVAILABLE" in str(exc)
            if not (is_server_error and is_unavailable):
                raise

            if attempt == max_retries - 1:
                raise RuntimeError(
                    "Gemini API sigue saturada tras varios intentos. Prueba en unos minutos."
                ) from exc

            wait_seconds = min(2 ** attempt, 16)
            print(
                f"Gemini saturado (intento {attempt + 1}/{max_retries}). "
                f"Reintentando en {wait_seconds}s..."
            )
            time.sleep(wait_seconds)


if __name__ == "__main__":
    main()
