#!/usr/bin/env bash

set -e

echo "🚀 Iniciando bootstrap del proyecto BOE Oposiciones..."

# 1. Crear venv si no existe
if [ ! -d ".venv" ]; then
  echo "📦 Creando entorno virtual '.venv'..."
  if command -v python3 &>/dev/null; then
    python3 -m venv .venv
  else
    python -m venv .venv
  fi
else
  echo "✅ Entorno virtual '.venv' ya existe."
fi

# 2. Activar venv
echo "🧪 Activando entorno virtual..."
# shellcheck disable=SC1091
source .venv/bin/activate

# 3. Instalar dependencias
if [ -f "requirements.txt" ]; then
  echo "📥 Instalando dependencias desde requirements.txt..."
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "⚠️ No se encontró requirements.txt, instalando desde setup.py..."
  pip install --upgrade pip
  pip install -e .
fi

# 4. Crear carpetas necesarias
echo "📁 Creando estructura de directorios..."
mkdir -p static/uploads/profiles

echo "✅ Bootstrap completado."
echo
echo "Para arrancar la aplicación:"
echo "1) Activar la venv: source .venv/bin/activate"
echo "2) Ejecutar: .venv/bin/python run.py"
