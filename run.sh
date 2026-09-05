#!/usr/bin/env bash
# Arranca el banco de pruebas en macOS o Linux usando conda.
# El equivalente para Windows es run.ps1.
set -euo pipefail

cd "$(dirname "$0")"

ENV_NAME="${ENV_NAME:-qa-framework}"

if ! command -v conda >/dev/null 2>&1; then
  echo "No encuentro 'conda' en el PATH." >&2
  exit 1
fi

eval "$(conda shell.bash hook)"

if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "Creando el entorno conda '$ENV_NAME'… (tarda un par de minutos)"
  conda env create -f environment.yml -n "$ENV_NAME"
fi

conda activate "$ENV_NAME"

python -m pip install --quiet --disable-pip-version-check -r requirements.txt

if [ ! -f .env ]; then
  echo "No hay .env. Copiando desde .env.example."
  cp .env.example .env
  echo "Edita .env y pon tu ANTHROPIC_API_KEY antes de continuar."
  exit 1
fi

export PYTHONIOENCODING=utf-8

exec python -m uvicorn app.main:app --reload --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
