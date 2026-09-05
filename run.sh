#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creando entorno virtual…"
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt
fi

if [ ! -f .env ]; then
  echo "No hay .env. Copiando desde .env.example."
  cp .env.example .env
  echo "Edita .env y pon tu ANTHROPIC_API_KEY antes de continuar."
  exit 1
fi

exec ./.venv/bin/uvicorn app.main:app --reload --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
