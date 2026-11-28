"""El tablero de Clientes en la base: las columnas con sus tarjetas, los números del embudo y el cambio de etapa a mano.

`CommerceStore` lo expone (`pipeline`, `move_customer`); aquí están sus consultas. Como el resto de clientes y ventas, solo cuenta las
conversaciones de canales reales del negocio que recibe.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.engine import Connection, Engine

from app.domain.business_config.commerce import ALL_STAGES, LOST, Customer
from app.domain.business_config.customer_card import SOURCE_TEAM
from app.domain.business_config.errors import ConversationNotFoundError
from app.domain.business_config.pipeline import (
    CARDS_PER_STAGE,
    CLOSE_TIME_DAYS,
    OPEN_STAGES,
    WON_DAYS,
    Pipeline,
    PipelineStats,
    StageColumn,
    StageMove,
    advance_rates,
    close_rate,
)
from app.infrastructure.business_config.commerce_queries import TEST_CHANNEL, bounds, customers_of, real_customers, utc
from app.infrastructure.business_config.customer_events import record_stage_change
from app.infrastructure.business_config.tables import conversations, sales
from app.infrastructure.business_config.tenancy import tenant_of


def read_pipeline(engine: Engine, tenant_slug: str, *, query: str | None, label: str | None = None, today: date) -> Pipeline:
    """Las columnas (con `query` o `label`, solo quienes coinciden) y los números del embudo, que cuentan a todos."""
    with engine.connect() as conn:
        tenant = tenant_of(conn, tenant_slug)
        shown = _counts(conn, real_customers(tenant.id, query, label))
        values = _values(conn, real_customers(tenant.id, query, label))
        columns = []
        for stage in ALL_STAGES:
            rows = conn.execute(
                select(conversations)
                .where(*real_customers(tenant.id, query, label), conversations.c.stage == stage)
                .order_by(conversations.c.last_message_at.desc())
                .limit(CARDS_PER_STAGE)
            ).all() if shown.get(stage) else []
            columns.append(StageColumn(stage, shown.get(stage, 0), customers_of(conn, rows), value=values.get(stage, {})))
        searching = bool(query and str(query).strip()) or bool(label)
        everyone = _counts(conn, real_customers(tenant.id)) if searching else shown
        all_values = _values(conn, real_customers(tenant.id)) if searching else values
        open_value: dict[str, Decimal] = {}
        for stage in OPEN_STAGES:
            for currency, amount in all_values.get(stage, {}).items():
                open_value[currency] = open_value.get(currency, Decimal(0)) + amount
        won_count, won = _won(conn, tenant.id, today)
        stats = PipelineStats(
            open_count=sum(everyone.get(stage, 0) for stage in OPEN_STAGES),
            open_value=open_value,
            lost_count=everyone.get(LOST, 0),
            won_count=won_count,
            won=won,
            close_rate=close_rate(everyone),
            days_to_buy=_days_to_buy(conn, tenant.id, today),
            advance=advance_rates(everyone),
        )
    return Pipeline(columns, stats)


def _counts(conn: Connection, where: list[Any]) -> dict[str, int]:
    rows = conn.execute(select(conversations.c.stage, func.count().label("n")).where(*where).group_by(conversations.c.stage))
    return {(row.stage or "new"): int(row.n) for row in rows}


def _values(conn: Connection, where: list[Any]) -> dict[str, dict[str, Decimal]]:
    """Lo que suman los valores de los clientes de cada etapa, por moneda."""
    rows = conn.execute(
        select(conversations.c.stage, conversations.c.deal_currency, func.sum(conversations.c.deal_amount).label("total"))
        .where(*where, conversations.c.deal_amount.is_not(None), conversations.c.deal_currency.is_not(None))
        .group_by(conversations.c.stage, conversations.c.deal_currency)
    )
    totals: dict[str, dict[str, Decimal]] = {}
    for row in rows:
        totals.setdefault(row.stage or "new", {})[row.deal_currency] = Decimal(row.total)
    return totals


def _won(conn: Connection, tenant_id: Any, today: date) -> tuple[int, dict[str, Decimal]]:
    """Las ventas confirmadas de los últimos `WON_DAYS` días (hoy incluido): cuántas y cuánto suman por moneda."""
    start, _ = bounds(today - timedelta(days=WON_DAYS - 1), today)
    rows = conn.execute(
        select(sales.c.currency, func.sum(sales.c.amount).label("total"), func.count().label("n"))
        .where(sales.c.tenant_id == tenant_id, sales.c.status == "confirmed", sales.c.created_at >= start)
        .group_by(sales.c.currency)
    ).all()
    return sum(int(row.n) for row in rows), {row.currency: Decimal(row.total) for row in rows}


def _days_to_buy(conn: Connection, tenant_id: Any, today: date) -> float | None:
    """Días promedio entre el primer mensaje de un cliente y su primera compra, para las primeras compras de los últimos
    `CLOSE_TIME_DAYS` días."""
    start, _ = bounds(today - timedelta(days=CLOSE_TIME_DAYS - 1), today)
    rows = conn.execute(
        select(sales.c.conversation_id, func.min(sales.c.created_at).label("bought_at"), func.min(conversations.c.started_at).label("started_at"))
        .join(conversations, conversations.c.id == sales.c.conversation_id)
        .where(sales.c.tenant_id == tenant_id, sales.c.status == "confirmed", conversations.c.channel != TEST_CHANNEL)
        .group_by(sales.c.conversation_id)
    ).all()
    spans = [
        max(0.0, (utc(row.bought_at) - utc(row.started_at)).total_seconds() / 86400)
        for row in rows
        if row.bought_at is not None and row.started_at is not None and utc(row.bought_at) >= start
    ]
    return round(sum(spans) / len(spans), 1) if spans else None


def move_customer(engine: Engine, tenant_slug: str, conversation_id: str, move: StageMove, *, by: str | None = None) -> Customer:
    """El equipo pasa al cliente a otra etapa. En «no compró» quedan el motivo y la fecha; al salir de ahí, se borran. El cambio
    queda en el historial de su ficha, a nombre de `by`."""
    try:
        key = uuid.UUID(str(conversation_id))
    except ValueError as exc:
        raise ConversationNotFoundError("ese cliente no existe") from exc
    now = datetime.now(timezone.utc)
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        mine = [conversations.c.id == key, *real_customers(tenant.id)]
        before = conn.execute(select(conversations.c.stage).where(*mine)).first()
        if before is None:
            raise ConversationNotFoundError("ese cliente no existe o es de otro negocio")
        lost = move.stage == LOST
        changes: dict[str, Any] = {"stage": move.stage, "lost_reason": move.lost_reason if lost else None, "lost_at": now if lost else None, "updated_at": now}
        if record_stage_change(
            conn, tenant_id=tenant.id, conversation_id=key, from_stage=before.stage, to_stage=move.stage, source=SOURCE_TEAM,
            detail=move.lost_reason, actor=by, at=now,
        ):
            changes["stage_changed_at"] = now
        conn.execute(update(conversations).where(*mine).values(**changes))
        row = conn.execute(select(conversations).where(*mine)).one()
        return customers_of(conn, [row])[0]
