"""Las conversaciones de cada negocio en `conversations` y `conversation_entries` (implementa `ConversationStorage`).

Cuando un intercambio trae el traspaso a una persona, la conversación queda esperando a alguien del equipo y se crea un aviso en
`notifications`, en la misma transacción. Mientras siga esperando no se crean más avisos: el equipo recibe uno por cada espera.
"""
from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.conversations import AUTHORS, CHANNELS, BusinessActivity, ChatMessage, ConversationSummary, NewMessage, preview
from app.domain.business_config.errors import ConversationNotFoundError
from app.infrastructure.business_config.tables import conversation_entries, conversations, notifications, tenants
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
    conversations.c.needs_human,
    conversations.c.handoff_requested_at,
)


def _utc(value: datetime | None) -> datetime | None:
    # SQLite devuelve fechas sin zona; todas se guardan en UTC.
    if value is None:
        return None
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
        needs_human=bool(row.needs_human),
        handoff_requested_at=_utc(row.handoff_requested_at),
    )


def _handoff_title(channel: str, contact_name: str | None) -> str:
    who = contact_name or "Un cliente"
    return f"Prueba: {who} pidió hablar con una persona" if channel == "prueba" else f"{who} pidió hablar con una persona"


class ConversationStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record(
        self,
        tenant_slug: str,
        *,
        channel: str,
        contact_ref: str,
        contact_name: str | None,
        messages: list[NewMessage],
        handoff: bool = False,
    ) -> str:
        if channel not in CHANNELS:
            raise ValueError(f"canal desconocido: {channel}")
        if any(message.author not in AUTHORS for message in messages):
            raise ValueError("autor de mensaje desconocido")
        if not messages:
            raise ValueError("no hay mensajes para guardar")
        for attempt in range(2):
            try:
                return self._record(tenant_slug, channel, contact_ref, contact_name, messages, handoff)
            except IntegrityError:
                # Otro proceso creó el mismo hilo a la vez: se repite y esta vez se encuentra.
                if attempt:
                    raise
        raise AssertionError("inalcanzable")

    def _record(self, tenant_slug: str, channel: str, contact_ref: str, contact_name: str | None, messages: list[NewMessage], handoff: bool) -> str:
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            key = and_(conversations.c.tenant_id == tenant.id, conversations.c.channel == channel, conversations.c.contact_ref == contact_ref)
            current = conn.execute(select(conversations.c.id, conversations.c.needs_human, conversations.c.contact_name).where(key)).first()
            if current is None:
                conversation_id = uuid.uuid4()
                already_waiting = False
                name = contact_name
                conn.execute(
                    insert(conversations).values(
                        id=conversation_id, tenant_id=tenant.id, channel=channel, contact_ref=contact_ref, contact_name=contact_name,
                        status="open", started_at=now, last_message_at=now, message_count=0, needs_human=False,
                    )
                )
            else:
                conversation_id, already_waiting, name = current.id, bool(current.needs_human), contact_name or current.contact_name
            conn.execute(
                insert(conversation_entries),
                [
                    # Un microsegundo entre mensajes del mismo intercambio: el hilo siempre conserva su orden.
                    {"id": uuid.uuid4(), "conversation_id": conversation_id, "author": message.author, "body": message.body, "intent": message.intent, "created_at": now + timedelta(microseconds=index)}
                    for index, message in enumerate(messages)
                ],
            )
            changes = {
                "last_message_at": now,
                "last_message_preview": preview(messages[-1].body),
                "message_count": conversations.c.message_count + len(messages),
                **({"contact_name": contact_name} if contact_name else {}),
            }
            if handoff and not already_waiting:
                changes.update(needs_human=True, handoff_requested_at=now)
                asked = next((message.body for message in messages if message.author == "customer"), None)
                conn.execute(
                    insert(notifications).values(
                        id=uuid.uuid4(), tenant_id=tenant.id, conversation_id=conversation_id, kind="handoff",
                        title=_handoff_title(channel, name), body=preview(asked) if asked else None, created_at=now,
                    )
                )
            conn.execute(update(conversations).where(conversations.c.id == conversation_id).values(**changes))
        return str(conversation_id)

    def recent(self, tenant_slugs: Collection[str], *, channel: str | None, limit: int, needs_human: bool | None = None) -> list[ConversationSummary]:
        query = select(*_SUMMARY).join(tenants, tenants.c.id == conversations.c.tenant_id).where(tenants.c.slug.in_(list(tenant_slugs)))
        if channel is not None:
            query = query.where(conversations.c.channel == channel)
        if needs_human is not None:
            query = query.where(conversations.c.needs_human.is_(needs_human))
        query = query.order_by(conversations.c.last_message_at.desc()).limit(limit)
        with self._engine.connect() as conn:
            return [_summary(row) for row in conn.execute(query)]

    def _key(self, conversation_id: str) -> uuid.UUID:
        try:
            return uuid.UUID(str(conversation_id))
        except ValueError as exc:
            raise ConversationNotFoundError("identificador no válido") from exc

    def thread(self, conversation_id: str) -> tuple[ConversationSummary, list[ChatMessage]]:
        key = self._key(conversation_id)
        with self._engine.connect() as conn:
            row = conn.execute(select(*_SUMMARY).join(tenants, tenants.c.id == conversations.c.tenant_id).where(conversations.c.id == key)).first()
            if row is None:
                raise ConversationNotFoundError("la conversación no existe")
            entries = conn.execute(select(conversation_entries).where(conversation_entries.c.conversation_id == key).order_by(conversation_entries.c.created_at)).all()
        messages = [ChatMessage(str(entry.id), entry.author, entry.body, _utc(entry.created_at), entry.intent) for entry in entries]
        return _summary(row), messages

    def business_of(self, conversation_id: str) -> str:
        """El negocio de la conversación, para comprobar el acceso antes de cambiarla."""
        key = self._key(conversation_id)
        with self._engine.connect() as conn:
            slug = conn.execute(select(tenants.c.slug).join(conversations, conversations.c.tenant_id == tenants.c.id).where(conversations.c.id == key)).scalar_one_or_none()
        if slug is None:
            raise ConversationNotFoundError("la conversación no existe")
        return slug

    def resolve_handoff(self, conversation_id: str) -> None:
        """Alguien del equipo ya atendió a quien pidió una persona: deja de esperar."""
        with self._engine.begin() as conn:
            conn.execute(update(conversations).where(conversations.c.id == self._key(conversation_id)).values(needs_human=False))

    def activity(self, tenant_slug: str, *, since: datetime) -> BusinessActivity:
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            mine = conversations.c.tenant_id == tenant.id

            def count(*conditions) -> int:
                return conn.execute(select(func.count()).select_from(conversations).where(mine, *conditions)).scalar_one()

            messages = conn.execute(
                select(func.count())
                .select_from(conversation_entries.join(conversations, conversations.c.id == conversation_entries.c.conversation_id))
                .where(mine, conversation_entries.c.created_at >= since)
            ).scalar_one()
            return BusinessActivity(
                conversations=count(),
                conversations_since=count(conversations.c.last_message_at >= since),
                messages_since=messages,
                test_conversations=count(conversations.c.channel == "prueba"),
                waiting_human=count(conversations.c.needs_human.is_(True)),
            )
