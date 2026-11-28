"""Clientes, ventas y reportes de cada negocio en la base (implementa `CommerceStorage`).

Los clientes salen de las conversaciones de canales reales (las pruebas del panel no cuentan), con la etapa que guarda cada
conversación. Las ventas viven en `sales`. Los reportes cuentan por día en la hora de Colombia (`REPORT_TIMEZONE`). Cada consulta
recibe el negocio y solo alcanza sus filas. Lo que comparte con el tablero está en `commerce_queries.py`; las consultas del tablero,
en `pipeline_store.py`.
"""
from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, insert, select, update
from sqlalchemy.engine import Connection, Engine

from app.domain.business_config.commerce import ALL_STAGES, STAGES, Customer, NewSale, ReportDay, ReportTotals, Sale, SaleError, reached
from app.domain.business_config.customer_card import SOURCE_SALE, CustomerCard, CustomerNote, DealChange, money_text
from app.domain.business_config.customer_labels import Label, LabelChange
from app.domain.business_config.errors import ConversationNotFoundError
from app.domain.business_config.reminders import NewReminder, Reminder
from app.domain.business_config.pipeline import Pipeline, StageMove
from app.infrastructure.business_config.commerce_queries import MAX_CUSTOMERS, TEST_CHANNEL, bounds, customers_of, day_of, real_customers, sale_of
from app.infrastructure.business_config.customer_card_store import add_note, delete_note, read_card, update_deal
from app.infrastructure.business_config.customer_events import record_stage_change
from app.infrastructure.business_config.label_store import create_label, delete_label, list_labels, set_customer_labels, update_label
from app.infrastructure.business_config.pipeline_store import move_customer, read_pipeline
from app.infrastructure.business_config.reminder_store import create_reminder, delete_reminder, list_reminders, set_reminder_done
from app.infrastructure.business_config.tables import conversation_entries, conversations, sales
from app.infrastructure.business_config.tenancy import tenant_of


class CommerceStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------ clientes

    def customers(
        self, tenant_slug: str, *, stage: str | None = None, query: str | None = None, label: str | None = None, limit: int = MAX_CUSTOMERS,
    ) -> list[Customer]:
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            where = real_customers(tenant.id, query, label)
            if stage in ALL_STAGES:
                where.append(conversations.c.stage == stage)
            rows = conn.execute(
                select(conversations).where(*where).order_by(conversations.c.last_message_at.desc()).limit(max(1, min(limit, MAX_CUSTOMERS)))
            ).all()
            return customers_of(conn, rows)

    # ------------------------------------------------------------------ el tablero (las consultas están en `pipeline_store.py`)

    def pipeline(self, tenant_slug: str, *, query: str | None = None, label: str | None = None, today: date) -> Pipeline:
        return read_pipeline(self._engine, tenant_slug, query=query, label=label, today=today)

    def move_customer(self, tenant_slug: str, conversation_id: str, move: StageMove, *, by: str | None = None) -> Customer:
        return move_customer(self._engine, tenant_slug, conversation_id, move, by=by)

    # ------------------------------------------------------------------ la ficha (las consultas están en `customer_card_store.py`)

    def customer_card(self, tenant_slug: str, conversation_id: str) -> CustomerCard:
        return read_card(self._engine, tenant_slug, conversation_id)

    def update_customer_deal(self, tenant_slug: str, conversation_id: str, change: DealChange, *, by: str | None = None) -> CustomerCard:
        return update_deal(self._engine, tenant_slug, conversation_id, change, by=by)

    def add_customer_note(self, tenant_slug: str, conversation_id: str, body: str, *, author: str | None = None) -> CustomerNote:
        return add_note(self._engine, tenant_slug, conversation_id, body, author=author)

    def delete_customer_note(self, tenant_slug: str, conversation_id: str, note_id: str) -> None:
        delete_note(self._engine, tenant_slug, conversation_id, note_id)

    # ------------------------------------------------------------------ las etiquetas (las consultas están en `label_store.py`)

    def labels(self, tenant_slug: str) -> list[Label]:
        return list_labels(self._engine, tenant_slug)

    def create_label(self, tenant_slug: str, name: str, color: str, *, created_by: str | None = None) -> Label:
        return create_label(self._engine, tenant_slug, name, color, created_by=created_by)

    def update_label(self, tenant_slug: str, label_id: str, change: LabelChange) -> Label:
        return update_label(self._engine, tenant_slug, label_id, change)

    def delete_label(self, tenant_slug: str, label_id: str) -> None:
        delete_label(self._engine, tenant_slug, label_id)

    def set_customer_labels(self, tenant_slug: str, conversation_id: str, label_ids: list[str]) -> Customer:
        return set_customer_labels(self._engine, tenant_slug, conversation_id, label_ids)

    # ------------------------------------------------------------------ los recordatorios (las consultas están en `reminder_store.py`)

    def reminders(self, tenant_slug: str, *, done: bool, assignee_id: str | None = None) -> list[Reminder]:
        return list_reminders(self._engine, tenant_slug, done=done, assignee_id=assignee_id)

    def create_reminder(self, tenant_slug: str, conversation_id: str, reminder: NewReminder, *, by_user: str | None, by: str | None) -> Reminder:
        return create_reminder(self._engine, tenant_slug, conversation_id, reminder, by_user=by_user, by=by)

    def set_reminder_done(self, tenant_slug: str, reminder_id: str, done: bool, *, by: str | None) -> Reminder:
        return set_reminder_done(self._engine, tenant_slug, reminder_id, done, by=by)

    def delete_reminder(self, tenant_slug: str, reminder_id: str) -> None:
        delete_reminder(self._engine, tenant_slug, reminder_id)

    # ------------------------------------------------------------------ ventas

    def record_sale(self, tenant_slug: str, sale: NewSale, *, created_by: str | None) -> Sale:
        """Registra la venta. Si es de una conversación, su cliente pasa a «cliente» y deja de esperar la verificación del pago."""
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            conversation_id = self._conversation_of(conn, tenant.id, sale.conversation_id) if sale.conversation_id else None
            sale_id = uuid.uuid4()
            conn.execute(
                insert(sales).values(
                    id=sale_id, tenant_id=tenant.id, conversation_id=conversation_id, customer_name=sale.customer_name,
                    description=sale.description, amount=sale.amount, currency=sale.currency, status="confirmed", created_by=created_by,
                    created_at=now,
                )
            )
            if conversation_id is not None:
                before = conn.execute(select(conversations.c.stage).where(conversations.c.id == conversation_id)).scalar_one()
                changes: dict[str, Any] = {"stage": "customer", "updated_at": now}
                if record_stage_change(
                    conn, tenant_id=tenant.id, conversation_id=conversation_id, from_stage=before, to_stage="customer", source=SOURCE_SALE,
                    detail=f"{sale.description} · {money_text(sale.amount, sale.currency)}", actor=created_by, at=now,
                ):
                    changes["stage_changed_at"] = now
                conn.execute(update(conversations).where(conversations.c.id == conversation_id).values(**changes))
                conn.execute(
                    update(conversations)
                    .where(conversations.c.id == conversation_id, conversations.c.handoff_reason == "payment_review")
                    .values(needs_human=False)
                )
            row = conn.execute(select(sales).where(sales.c.id == sale_id)).one()
        return sale_of(row)

    @staticmethod
    def _conversation_of(conn: Connection, tenant_id: Any, conversation_id: str) -> Any:
        try:
            key = uuid.UUID(str(conversation_id))
        except ValueError as exc:
            raise ConversationNotFoundError("la conversación no existe") from exc
        found = conn.execute(select(conversations.c.id).where(conversations.c.id == key, conversations.c.tenant_id == tenant_id)).scalar_one_or_none()
        if found is None:
            raise ConversationNotFoundError("la conversación no existe o es de otro negocio")
        return found

    def cancel_sale(self, tenant_slug: str, sale_id: str) -> Sale:
        try:
            key = uuid.UUID(str(sale_id))
        except ValueError as exc:
            raise SaleError("sale", "Esa venta no existe.") from exc
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            mine = and_(sales.c.id == key, sales.c.tenant_id == tenant.id)
            if conn.execute(select(sales.c.id).where(mine)).first() is None:
                raise SaleError("sale", "Esa venta no existe.")
            conn.execute(update(sales).where(mine, sales.c.status == "confirmed").values(status="cancelled", cancelled_at=datetime.now(timezone.utc)))
            return sale_of(conn.execute(select(sales).where(mine)).one())

    def sales(self, tenant_slug: str, *, since: date, limit: int = 500) -> list[Sale]:
        start, _end = bounds(since, since)
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            rows = conn.execute(
                select(sales).where(sales.c.tenant_id == tenant.id, sales.c.created_at >= start).order_by(sales.c.created_at.desc()).limit(limit)
            ).all()
        return [sale_of(row) for row in rows]

    # ------------------------------------------------------------------ reportes

    def report_data(self, tenant_slug: str, *, since: date, until: date) -> tuple[list[ReportDay], ReportTotals, dict[str, int], dict[str, int]]:
        """Por día y en total: conversaciones nuevas, mensajes por autor y ventas; el embudo y los pasos a una persona."""
        start, end = bounds(since, until)
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            real = and_(conversations.c.tenant_id == tenant.id, conversations.c.channel != TEST_CHANNEL)
            started = conn.execute(select(conversations.c.started_at).where(real, conversations.c.started_at >= start, conversations.c.started_at < end)).scalars().all()
            entries = conn.execute(
                select(conversation_entries.c.created_at, conversation_entries.c.author)
                .join(conversations, conversations.c.id == conversation_entries.c.conversation_id)
                .where(real, conversation_entries.c.created_at >= start, conversation_entries.c.created_at < end)
            ).all()
            sold = conn.execute(
                select(sales.c.created_at, sales.c.amount, sales.c.currency)
                .where(sales.c.tenant_id == tenant.id, sales.c.status == "confirmed", sales.c.created_at >= start, sales.c.created_at < end)
            ).all()
            active = conn.execute(select(conversations.c.stage).where(real, conversations.c.last_message_at >= start, conversations.c.last_message_at < end)).scalars().all()
            handoffs = conn.execute(
                select(conversations.c.handoff_reason).where(real, conversations.c.handoff_requested_at >= start, conversations.c.handoff_requested_at < end)
            ).scalars().all()

        per_day: dict[date, dict[str, int]] = defaultdict(Counter)
        for moment in started:
            per_day[day_of(moment)]["new_conversations"] += 1
        for moment, author in entries:
            per_day[day_of(moment)][f"{author}_messages"] += 1
        revenue: dict[str, Decimal] = defaultdict(Decimal)
        for moment, amount, currency in sold:
            per_day[day_of(moment)]["sales"] += 1
            revenue[currency] += Decimal(amount)
        days = []
        current = since
        while current <= until:
            counts = per_day.get(current, {})
            days.append(
                ReportDay(
                    current, counts.get("new_conversations", 0), counts.get("customer_messages", 0), counts.get("assistant_messages", 0),
                    counts.get("agent_messages", 0), counts.get("sales", 0),
                )
            )
            current += timedelta(days=1)
        totals = ReportTotals(
            conversations=len(started),
            customer_messages=sum(day.customer_messages for day in days),
            assistant_messages=sum(day.assistant_messages for day in days),
            agent_messages=sum(day.agent_messages for day in days),
            handoffs=len(handoffs),
            sales=len(sold),
            revenue=dict(revenue),
        )
        funnel = {stage: sum(1 for value in active if reached(value or "new", stage)) for stage in STAGES}
        reasons = dict(Counter(reason or "human_request" for reason in handoffs))
        return days, totals, funnel, reasons
