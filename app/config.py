"""Configuración leída desde el entorno."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Ajustes de la aplicación. Todo viene del .env."""

    api_key: str = os.getenv("ANTHROPIC_API_KEY", "").strip()

    default_model: str = os.getenv("DEFAULT_MODEL", "claude-sonnet-5").strip()
    available_models: list[str] = [
        m.strip()
        for m in os.getenv(
            "AVAILABLE_MODELS",
            "claude-sonnet-5,claude-opus-5,claude-haiku-4-5-20251001",
        ).split(",")
        if m.strip()
    ]

    default_temperature: float = float(os.getenv("DEFAULT_TEMPERATURE", "1.0"))
    default_max_tokens: int = int(os.getenv("DEFAULT_MAX_TOKENS", "400"))
    default_effort: str = os.getenv("DEFAULT_EFFORT", "medium").strip()

    max_runs: int = int(os.getenv("MAX_RUNS", "20"))
    concurrency: int = int(os.getenv("CONCURRENCY", "6"))
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "60"))

    replay_mode: bool = _bool("REPLAY_MODE", False)
    data_dir: Path = BASE_DIR / os.getenv("DATA_DIR", "data")

    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
