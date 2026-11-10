"""Cuánto gasta cada negocio en inteligencia artificial: respuestas y tokens por día y modelo, con el costo si OpenRouter lo informa.

Cada negocio paga su propia clave de OpenRouter; el panel le muestra su consumo para que no tenga sorpresas en la factura.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AIUsage:
    """Lo que costó una respuesta del modelo."""

    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float | None = None

    def __post_init__(self) -> None:
        if self.prompt_tokens < 0 or self.completion_tokens < 0:
            raise ValueError("los tokens no pueden ser negativos")


@dataclass(frozen=True)
class DailyAIUsage:
    day: date
    replies: int
    prompt_tokens: int
    completion_tokens: int


@dataclass(frozen=True)
class AIUsageSummary:
    """El consumo de un negocio desde `since` (incluido). `cost_usd` es None si OpenRouter nunca informó el costo."""

    since: date
    replies: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float | None
    days: list[DailyAIUsage]

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens
