# =========================================================
# Pequeña mejora: dejo preparado el modo debug para desarrollo
# =========================================================

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)