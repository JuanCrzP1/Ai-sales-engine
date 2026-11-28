"""El historial de la ficha de cada cliente (`customer_events`): lo anota, en su misma transacción, cada parte que cambia algo.

La etapa cambia en cinco lugares y todos pasan por `record_stage_change`: el asistente al reconocer algo en el chat y al recibir el
aviso de un pago (`conversation_store.py`), el equipo al mover al cliente en el tablero (`pipeline_store.py`) y al confirmar un
pago (`conversation_store.finish_payment`), y una venta registrada (`commerce_store.record_sale`).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import insert
from sqlalchemy.engine import Connection

from app.domain.business_config.customer_card import EVENT_STAGE
from app.infrastructure.business_config.tables import customer_events


def record_event(
    conn: Connection, *, tenant_id: Any, conversation_id: Any, kind: str, source: str, from_stage: str | None = None,
    to_stage: str | None = None, detail: str | None = None, actor: str | None = None, at: datetime | None = None,
) -> None:
    conn.execute(
        insert(customer_events).values(
            id=uuid.uuid4(), tenant_id=tenant_id, conversation_id=conversation_id, kind=kind, source=source, from_stage=from_stage,
            to_stage=to_stage, detail=detail, actor=actor, created_at=at or datetime.now(timezone.utc),
        )
    )


def record_stage_change(
    conn: Connection, *, tenant_id: Any, conversation_id: Any, from_stage: str | None, to_stage: str, source: str,
    detail: str | None = None, actor: str | None = None, at: datetime | None = None,
) -> bool:
    """Anota el cambio de etapa, si de verdad cambió. Devuelve si lo anotó."""
    if (from_stage or "new") == to_stage:
        return False
    record_event(
        conn, tenant_id=tenant_id, conversation_id=conversation_id, kind=EVENT_STAGE, source=source, from_stage=from_stage or "new",
        to_stage=to_stage, detail=detail, actor=actor, at=at,
    )
    return True
