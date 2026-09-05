"""Cliente asíncrono de la API de Anthropic.

Nota sobre el muestreo, que importa para la demo de consistencia:

Los modelos de la generación Sonnet 5 / Opus 5 gestionan el muestreo por su
cuenta y rechazan `temperature`, `top_p` y `top_k` con un 400. El control
equivalente hoy es `output_config.effort`, que va en el nivel superior de la
petición y no dentro de `thinking`.

Este cliente hace dos cosas para que eso no reviente una demo en vivo:

  1. No manda `temperature` a los modelos que se sabe que la rechazan.
  2. Si aun así la API devuelve un 400 quejándose del parámetro, reintenta
     una vez sin él en vez de pintar un error rojo en pantalla.

El punto pedagógico es bueno: ya no puedes fijar la temperatura en cero para
esconder la variación. El modelo decide su propio muestreo, y la variación
sigue ahí.
"""
from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass

from anthropic import APIStatusError, AsyncAnthropic

from .config import Settings

# Familias que gestionan el muestreo solas y rechazan temperature.
_NO_TEMPERATURE = re.compile(
    r"(sonnet-5|opus-5|fable-5|mythos-5|opus-4-7|opus-4-8)", re.IGNORECASE
)

_SAMPLING_COMPLAINT = re.compile(r"temperature|top_p|top_k|sampling", re.IGNORECASE)


def accepts_temperature(model: str) -> bool:
    return not _NO_TEMPERATURE.search(model or "")


class ClientError(Exception):
    """Error ya redactado para mostrarse en pantalla durante la ponencia."""


@dataclass(slots=True)
class Completion:
    text: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    temperature_dropped: bool = False


class ClaudeClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncAnthropic | None = None
        if settings.has_key:
            self._client = AsyncAnthropic(
                api_key=settings.api_key,
                timeout=settings.request_timeout,
                max_retries=1,
            )

    def _payload(
        self,
        prompt: str,
        system: str | None,
        model: str,
        temperature: float | None,
        max_tokens: int | None,
        effort: str | None,
        with_temperature: bool,
    ) -> dict:
        payload: dict = {
            "model": model,
            "max_tokens": max_tokens or self._settings.default_max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system and system.strip():
            payload["system"] = system.strip()

        chosen = effort or self._settings.default_effort
        if chosen and chosen != "default":
            payload["output_config"] = {"effort": chosen}

        if with_temperature and accepts_temperature(model):
            payload["temperature"] = (
                self._settings.default_temperature
                if temperature is None
                else temperature
            )

        return payload

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        effort: str | None = None,
    ) -> Completion:
        if self._client is None:
            raise ClientError(
                "No hay llave de API configurada. Copia .env.example a .env "
                "y pon tu ANTHROPIC_API_KEY."
            )

        target = model or self._settings.default_model
        dropped = not accepts_temperature(target)
        started = time.perf_counter()
        message = None

        for send_temperature in (True, False):
            payload = self._payload(
                prompt, system, target, temperature, max_tokens, effort,
                with_temperature=send_temperature,
            )
            try:
                message = await self._client.messages.create(**payload)
                break
            except APIStatusError as exc:
                if (
                    send_temperature
                    and exc.status_code == 400
                    and _SAMPLING_COMPLAINT.search(str(exc))
                ):
                    dropped = True
                    continue
                raise ClientError(
                    f"La API respondió {exc.status_code}. {exc.message}"
                ) from exc
            except asyncio.TimeoutError as exc:
                raise ClientError("La API no respondió a tiempo.") from exc
            except Exception as exc:
                raise ClientError(f"No se pudo llamar a la API. {exc}") from exc

        if message is None:
            raise ClientError("La API rechazó la petición.")

        elapsed = int((time.perf_counter() - started) * 1000)
        text = "\n".join(
            block.text for block in message.content if block.type == "text"
        ).strip()

        return Completion(
            text=text,
            latency_ms=elapsed,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            temperature_dropped=dropped,
        )

    async def complete_many(
        self,
        prompt: str,
        runs: int,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        effort: str | None = None,
    ) -> list[Completion | ClientError]:
        """N llamadas en paralelo con tope de concurrencia.

        Los fallos vuelven como excepción dentro de la lista, en su posición,
        para que una ejecución caída no tumbe la demo entera.
        """
        gate = asyncio.Semaphore(self._settings.concurrency)

        async def one() -> Completion | ClientError:
            async with gate:
                try:
                    return await self.complete(
                        prompt, system, model, temperature, max_tokens, effort
                    )
                except ClientError as exc:
                    return exc

        return await asyncio.gather(*(one() for _ in range(runs)))
