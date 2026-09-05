"""Modo repetición: sirve respuestas guardadas cuando la red falla.

La red de una sala de conferencias es el riesgo más real de una demo en vivo.
Este módulo guarda cada corrida en disco. Si el día del evento algo falla,
se activa el modo repetición y la interfaz se comporta igual, sirviendo las
respuestas de la última corrida buena.
"""
from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path


class ReplayStore:
    def __init__(self, directory: Path) -> None:
        self._dir = directory
        self._dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _slug(prompt: str, system: str | None = None) -> str:
        raw = f"{(system or '').strip()}||{prompt.strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _path(self, prompt: str, system: str | None = None) -> Path:
        return self._dir / f"{self._slug(prompt, system)}.json"

    def save(
        self,
        prompt: str,
        responses: list[str],
        system: str | None = None,
        model: str = "",
    ) -> None:
        if not responses:
            return
        payload = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "system": system or "",
            "model": model,
            "responses": responses,
        }
        self._path(prompt, system).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def load(self, prompt: str, system: str | None = None) -> list[str]:
        path = self._path(prompt, system)
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("responses", [])
        except (json.JSONDecodeError, OSError):
            return []

    def sample(self, prompt: str, system: str | None = None) -> str | None:
        responses = self.load(prompt, system)
        return random.choice(responses) if responses else None

    def take(self, prompt: str, count: int, system: str | None = None) -> list[str]:
        """Devuelve `count` respuestas, repitiendo si hay menos guardadas."""
        responses = self.load(prompt, system)
        if not responses:
            return []
        if len(responses) >= count:
            return responses[:count]
        return [responses[i % len(responses)] for i in range(count)]

    def listing(self) -> list[str]:
        entries = []
        for path in sorted(self._dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            prompt = data.get("prompt", "")
            preview = prompt[:70] + ("…" if len(prompt) > 70 else "")
            entries.append(f"{len(data.get('responses', []))}× {preview}")
        return entries
