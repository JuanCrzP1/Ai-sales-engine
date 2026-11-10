"""Las conversaciones de cada negocio en `conversations` y `conversation_entries` (implementa `ConversationStorage`)."""
from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.conversations import AUTHORS, CHANNELS, BusinessActivity, ChatMessage, ConversationSummary, NewMessage, preview
from app.domain.business_config.errors import ConversationNotFoundError
from app.infrastructure.business_config.tables import conversation_entries, conversations, tenants
from app.infrastructure.business_config.tenancy import tenant_of

_SUMMARY = (
    conversations.c.id,
    tenants.c.slug,
    tenants.c.name,
    conversations.c.channel,
    conversations.c.contact_name,
    conversations.c.status,
    conversations.c.started_at,
    conversations.c.last_message_at,
    conversations.c.last_message_preview,
    conversations.c.message_count,
)


def _utc(value: datetime) -> datetime:
    # SQLite devuelve fechas sin zona; todas se guardan en UTC.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _summary(row) -> ConversationSummary:
    return ConversationSummary(
        id=str(row.id),
        business_slug=row.slug,
        business_name=row.name,
        channel=row.channel,
        contact_name=row.contact_name,
        status=row.status,
        started_at=_utc(row.started_at),
        last_message_at=_utc(row.last_message_at),
        last_message_preview=row.last_message_preview,
        message_count=row.message_count,
    )


class ConversationStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record(self, tenant_slug: str, *, channel: str, contact_ref: str, contact_name: str | None, messages: list[NewMessage]) -> str:
        if channel not in CHANNELS:
            raise ValueError(f"canal desconocido: {channel}")
        if any(message.author not in AUTHORS for message in messages):
            raise ValueError("autor de mensaje desconocido")
        if not messages:
            raise ValueError("no hay mensajes para guardar")
        for attempt in range(2):
            try:
                return self._record(tenant_slug, channel, contact_ref, contact_name, messages)
            except IntegrityError:
                # Otro proceso creó el mismo hilo a la vez: se repite y esta vez se encuentra.
                if attempt:
                    raise
        raise AssertionError("inalcanzable")

    def _record(self, tenant_slug: str, channel: str, contact_ref: str, contact_name: str | None, messages: list[NewMessage]) -> str:
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            key = and_(conversations.c.tenant_id == tenant.id, conversations.c.channel == channel, conversations.c.contact_ref == contact_ref)
            conversation_id = conn.execute(select(conversations.c.id).where(key)).scalar_one_or_none()
            if conversation_id is None:
                conversation_id = uuid.uuid4()
                conn.execute(
                    insert(conversations).values(
                        id=conversation_id, tenant_id=tenant.id, channel=channel, contact_ref=contact_ref, contact_name=contact_name,
                        status="open", started_at=now, last_message_at=now, message_count=0,
                    )
                )
            conn.execute(
                insert(conversation_entries),
                [
                    # Un microsegundo entre mensajes del mismo intercambio: el hilo siempre conserva su orden.
                    {"id": uuid.uuid4(), "conversation_id": conversation_id, "author": message.author, "body": message.body, "intent": message.intent, "created_at": now + timedelta(microseconds=index)}
                    for index, message in enumerate(messages)
                ],
            )
            conn.execute(
                update(conversations)
                .where(conversations.c.id == conversation_id)
                .values(
                    last_message_at=now,
                    last_message_preview=preview(messages[-1].body),
                    message_count=conversations.c.message_count + len(messages),
                    **({"contact_name": contact_name} if contact_name else {}),
                )
            )
        return str(conversation_id)

    def recent(self, tenant_slugs: Collection[str], *, channel: str | None, limit: int) -> list[ConversationSummary]:
        query = select(*_SUMMARY).join(tenants, tenants.c.id == conversations.c.tenant_id).where(tenants.c.slug.in_(list(tenant_slugs)))
        if channel is not None:
            query = query.where(conversations.c.channel == channel)
        query = query.order_by(conversations.c.last_message_at.desc()).limit(limit)
        with self._engine.connect() as conn:
            return [_summary(row) for row in conn.execute(query)]

    def thread(self, conversation_id: str) -> tuple[ConversationSummary, list[ChatMessage]]:
        try:
            key = uuid.UUID(str(conversation_id))
        except ValueError as exc:
            raise ConversationNotFoundError("identificador no válido") from exc
        with self._engine.connect() as conn:
            row = conn.execute(select(*_SUMMARY).join(tenants, tenants.c.id == conversations.c.tenant_id).where(conversations.c.id == key)).first()
            if row is None:
                raise ConversationNotFoundError("la conversación no existe")
            entries = conn.execute(
                select(conversation_entries)
                .where(conversation_entries.c.conversation_id == key)
                .order_by(conversation_entries.c.created_at)
            ).all()
        messages = [ChatMessage(str(entry.id), entry.author, entry.body, _utc(entry.created_at), entry.intent) for entry in entries]
        return _summary(row), messages

    def activity(self, tenant_slug: str, *, since: datetime) -> BusinessActivity:
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            mine = conversations.c.tenant_id == tenant.id
            total = conn.execute(select(func.count()).select_from(conversations).where(mine)).scalar_one()
            recent = conn.execute(select(func.count()).select_from(conversations).where(mine, conversations.c.last_message_at >= since)).scalar_one()
            tests = conn.execute(select(func.count()).select_from(conversations).where(mine, conversations.c.channel == "prueba")).scalar_one()
            messages = conn.execute(
                select(func.count())
                .select_from(conversation_entries.join(conversations, conversations.c.id == conversation_entries.c.conversation_id))
                .where(mine, conversation_entries.c.created_at >= since)
            ).scalar_one()
        return BusinessActivity(conversations=total, conversations_since=recent, messages_since=messages, test_conversations=tests)
