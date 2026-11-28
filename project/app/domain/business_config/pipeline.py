"""El embudo de clientes: el tablero de Clientes, con una columna por etapa.

- **Columnas**: las etapas del embudo (`STAGES`) y, al final y fuera de él, «no compró» (`LOST`). Cada columna trae cuántos clientes
  tiene y sus tarjetas más recientes.
- **Mover**: el asistente avanza la etapa solo con lo que reconoce en el chat; el equipo puede mover a cualquier cliente a mano. A
  «cliente» no se mueve: se llega registrando su venta, para que el tablero y las ventas digan lo mismo. A «no compró» se pasa con
  un motivo opcional.
- **Números**: cuántos siguen en el embudo, lo vendido en 30 días, de cada 100 cuántos compran, cuánto tardan en comprar y qué parte
  de los que llegan a una etapa llega a la siguiente.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.business_config.commerce import ALL_STAGES, LOST, STAGES, Customer

CARDS_PER_STAGE = 30
MAX_LOST_REASON = 200
WON_DAYS = 30
CLOSE_TIME_DAYS = 90
# La etapa a la que solo se llega registrando la venta.
SOLD_STAGE = "customer"
OPEN_STAGES = tuple(stage for stage in STAGES if stage != SOLD_STAGE)


class StageMoveError(ValueError):
    """El cambio de etapa no sirve. `field` dice qué dato; el mensaje es para el negocio."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


@dataclass(frozen=True)
class StageMove:
    """Un cambio de etapa hecho por el equipo, ya revisado."""

    stage: str
    lost_reason: str | None = None

    @classmethod
    def checked(cls, *, stage: object, reason: object = None) -> StageMove:
        target = str(stage or "").strip().lower()
        if target not in ALL_STAGES:
            raise StageMoveError("stage", "Esa etapa no existe.")
        if target == SOLD_STAGE:
            raise StageMoveError("stage", "Para pasarlo a «Cliente», registra su venta.")
        why = " ".join(str(reason or "").split())
        if len(why) > MAX_LOST_REASON:
            raise StageMoveError("reason", f"El motivo es muy largo (máximo {MAX_LOST_REASON} caracteres).")
        return cls(target, (why or None) if target == LOST else None)


@dataclass(frozen=True)
class StageColumn:
    stage: str
    count: int
    # Las tarjetas más recientes de la etapa (hasta `CARDS_PER_STAGE`); `count` dice cuántos hay en total.
    customers: list[Customer] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineStats:
    # Clientes que siguen en el embudo sin comprar.
    open_count: int = 0
    lost_count: int = 0
    # Lo vendido en los últimos `WON_DAYS` días, por moneda (nunca se mezclan).
    won_count: int = 0
    won: dict[str, Decimal] = field(default_factory=dict)
    # De todos los clientes (también los que no compraron), qué parte compró: 0 a 1, o None si no hay nadie.
    close_rate: float | None = None
    # Días promedio desde el primer mensaje hasta la primera compra (compras de los últimos `CLOSE_TIME_DAYS` días).
    days_to_buy: float | None = None
    # De los que llegaron a cada etapa, qué parte llegó a la siguiente: 0 a 1, o None si nadie llegó a esa etapa.
    advance: dict[str, float | None] = field(default_factory=dict)


@dataclass(frozen=True)
class Pipeline:
    columns: list[StageColumn]
    stats: PipelineStats


def close_rate(counts: dict[str, int]) -> float | None:
    """De todos los clientes del tablero, qué parte compró."""
    total = sum(counts.get(stage, 0) for stage in ALL_STAGES)
    return counts.get(SOLD_STAGE, 0) / total if total else None


def advance_rates(counts: dict[str, int]) -> dict[str, float | None]:
    """De los que llegaron a cada etapa del embudo, qué parte llegó a la siguiente. Se cuenta acumulado: quien ya es cliente pasó por
    todas las anteriores. Los que no compraron quedan fuera: no se sabe hasta dónde llegaron."""
    reached = {stage: sum(counts.get(later, 0) for later in STAGES[index:]) for index, stage in enumerate(STAGES)}
    return {stage: (reached[following] / reached[stage] if reached[stage] else None) for stage, following in zip(STAGES, STAGES[1:])}
