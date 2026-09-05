"""Contratos de entrada y salida de la API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Effort = Literal["low", "medium", "high", "xhigh", "default"]


class AskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    system: str | None = Field(default=None, max_length=8000)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=1)
    effort: Effort | None = None
    max_tokens: int | None = Field(default=None, ge=16, le=4096)
    replay: bool = False


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class AskResponse(BaseModel):
    text: str
    model: str
    latency_ms: int
    from_replay: bool
    temperature_dropped: bool = False
    usage: Usage


class ConsistencyRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    system: str | None = Field(default=None, max_length=8000)
    runs: int = Field(default=10, ge=2, le=50)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=1)
    effort: Effort | None = None
    max_tokens: int | None = Field(default=None, ge=16, le=4096)
    replay: bool = False


class RunResult(BaseModel):
    index: int
    state: Literal["ok", "failed"]
    text: str
    latency_ms: int
    word_count: int = 0


class Metrics(BaseModel):
    lexical_divergence: int
    unique_responses: int
    key_facts: list[str]
    key_fact_divergence: int
    word_count_min: int
    word_count_max: int
    volatile_tokens: list[str]


class ConsistencyResponse(BaseModel):
    prompt: str
    model: str
    runs: list[RunResult]
    metrics: Metrics
    from_replay: bool
    temperature_dropped: bool = False
    total_latency_ms: int


class ConfigResponse(BaseModel):
    has_key: bool
    replay_mode: bool
    default_model: str
    available_models: list[str]
    default_temperature: float
    default_max_tokens: int
    default_effort: str
    max_runs: int
    saved_runs: list[str]
    temperature_models: list[str]
