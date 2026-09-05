"""Banco de pruebas de calidad en respuestas de IA.

Backend para las dos demostraciones en vivo de la ponencia
"Calidad en respuestas de IA: del wow al rigor".
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import metrics
from .claude_client import ClaudeClient, ClientError, Completion, accepts_temperature
from .config import BASE_DIR, get_settings
from .replay import ReplayStore
from .schemas import (
    AskRequest,
    AskResponse,
    ConfigResponse,
    ConsistencyRequest,
    ConsistencyResponse,
    Metrics,
    RunResult,
    Usage,
)

settings = get_settings()
store = ReplayStore(settings.data_dir)
client = ClaudeClient(settings)

STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    mode = "repetición" if settings.replay_mode else "en vivo"
    key = "configurada" if settings.has_key else "AUSENTE"
    print(f"\n  Banco de pruebas listo en http://{settings.host}:{settings.port}")
    print(f"  Modo: {mode}  ·  Llave: {key}  ·  Modelo: {settings.default_model}\n")
    yield


app = FastAPI(
    title="Banco de pruebas · Calidad en respuestas de IA",
    description="Backend de las demos en vivo de la ponencia QAConf.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/api/config", response_model=ConfigResponse)
async def read_config() -> ConfigResponse:
    """Lo que el frontend necesita saber al arrancar."""
    return ConfigResponse(
        has_key=settings.has_key,
        replay_mode=settings.replay_mode,
        default_model=settings.default_model,
        available_models=settings.available_models,
        default_temperature=settings.default_temperature,
        default_max_tokens=settings.default_max_tokens,
        default_effort=settings.default_effort,
        max_runs=settings.max_runs,
        saved_runs=store.listing(),
        temperature_models=[
            m for m in settings.available_models if accepts_temperature(m)
        ],
    )


@app.post("/api/ask", response_model=AskResponse)
async def ask(body: AskRequest) -> AskResponse:
    """Demo 1. Una pregunta, una respuesta."""
    use_replay = body.replay or settings.replay_mode

    if use_replay:
        saved = store.sample(body.prompt, body.system)
        if saved is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "No hay respuestas guardadas para esta pregunta. "
                    "Desactiva el modo repetición y corre la demo una vez."
                ),
            )
        return AskResponse(
            text=saved,
            model=body.model or settings.default_model,
            latency_ms=0,
            from_replay=True,
            usage=Usage(),
        )

    try:
        result = await client.complete(
            prompt=body.prompt,
            system=body.system,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            effort=body.effort,
        )
    except ClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    store.save(
        body.prompt,
        [result.text],
        body.system,
        body.model or settings.default_model,
    )

    return AskResponse(
        text=result.text,
        model=body.model or settings.default_model,
        latency_ms=result.latency_ms,
        from_replay=False,
        temperature_dropped=result.temperature_dropped,
        usage=Usage(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ),
    )


@app.post("/api/consistency", response_model=ConsistencyResponse)
async def consistency(body: ConsistencyRequest) -> ConsistencyResponse:
    """Demo 2. La misma pregunta N veces, con métricas de divergencia."""
    runs = min(body.runs, settings.max_runs)
    use_replay = body.replay or settings.replay_mode
    model = body.model or settings.default_model
    started = time.perf_counter()

    if use_replay:
        saved = store.take(body.prompt, runs, body.system)
        if not saved:
            raise HTTPException(
                status_code=409,
                detail=(
                    "No hay respuestas guardadas para esta pregunta. "
                    "Desactiva el modo repetición y corre la demo una vez."
                ),
            )
        results = [
            RunResult(
                index=i,
                state="ok",
                text=text,
                latency_ms=0,
                word_count=len(metrics.normalize(text)),
            )
            for i, text in enumerate(saved)
        ]
        return ConsistencyResponse(
            prompt=body.prompt,
            model=model,
            runs=results,
            metrics=Metrics(**metrics.summarize(saved)),
            from_replay=True,
            total_latency_ms=0,
        )

    outcomes = await client.complete_many(
        prompt=body.prompt,
        runs=runs,
        system=body.system,
        model=body.model,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        effort=body.effort,
    )

    results: list[RunResult] = []
    dropped = False
    successful: list[str] = []

    for index, outcome in enumerate(outcomes):
        if isinstance(outcome, Completion):
            successful.append(outcome.text)
            dropped = dropped or outcome.temperature_dropped
            results.append(
                RunResult(
                    index=index,
                    state="ok",
                    text=outcome.text,
                    latency_ms=outcome.latency_ms,
                    word_count=len(metrics.normalize(outcome.text)),
                )
            )
        else:
            results.append(
                RunResult(index=index, state="failed", text=str(outcome), latency_ms=0)
            )

    if not successful:
        raise HTTPException(
            status_code=502,
            detail=results[0].text if results else "Ninguna ejecución tuvo éxito.",
        )

    store.save(body.prompt, successful, body.system, model)

    return ConsistencyResponse(
        prompt=body.prompt,
        model=model,
        runs=results,
        metrics=Metrics(**metrics.summarize(successful)),
        from_replay=False,
        temperature_dropped=dropped,
        total_latency_ms=int((time.perf_counter() - started) * 1000),
    )


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "has_key": settings.has_key, "replay": settings.replay_mode}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
