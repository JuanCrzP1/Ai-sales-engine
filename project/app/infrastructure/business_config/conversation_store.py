"""Las conversaciones de cada negocio en `conversations`, `conversation_entries` y `conversation_media` (implementa
`ConversationStorage`).

Cada mensaje de un canal se guarda apenas llega o sale (`append`), con su tipo, su estado y el id que le dio el canal: el mismo aviso
repetido no se guarda dos veces (índice único por conversación). Cuando la conversación pasa a una persona, queda esperando a alguien
del equipo, la IA se pausa y se crea un aviso en `notifications`, en la misma transacción. Mientras siga esperando no se crean más
avisos: el equipo recibe uno por cada espera. Todo cambio anota `updated_at`, así el panel pide solo lo que cambió.

Atención humana (migración 0011): mientras la IA está pausada, `customer_waiting_since` dice desde cuándo el cliente espera sin
respuesta. Lo borra la respuesta del equipo, «Ya lo atendí» o la IA al retomar. La IA retoma un chat una sola vez por espera aunque
dos procesos lo intenten a la vez (`resume_waiting`), y después de retomarlo no se vuelve a pausar sola hasta que alguien del equipo
lo atienda: así un cliente que insiste en hablar con una persona no queda en pausa cada media hora.
"""
from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, delete, func, insert, select, update
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.conversations import (
    AUTHORS,
    CHANNELS,
    HANDOFF_REASONS,
    KINDS,
    MAX_MEDIA_BYTES,
    STATUSES,
    AppendResult,
    BusinessActivity,
    WaitingChat,
    ChatMessage,
    ConversationSummary,
    ConversationTarget,
    MediaFile,
    MediaInfo,
    NewMessage,
    advances,
    handoff_title,
    message_preview,
    preview,
)
from app.domain.business_config.commerce import advanced, stage_for_intent
from app.domain.business_config.errors import ConversationNotFoundError
from app.infrastructure.business_config.tables import conversation_entries, conversation_media, conversations, notifications, tenants
from app.infrastructure.business_config.tenancy import tenant_of

# Los canales en los que la IA retoma un chat que nadie atendió (las pruebas nunca esperan).
RESUMABLE_CHANNELS = ("whatsapp", "telegram", "api")
# El panel pide lo que cambió desde su última marca, con este margen: un cambio que se guardó justo en ese instante no se pierde.
LIVE_OVERLAP = timedelta(seconds=3)

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
    conversations.c.handoff_reason,
    conversations.c.handoff_summary,
    conversations.c.ai_paused,
    conversations.c.unread_count,
    conversations.c.assistant_typing_until,
    conversations.c.updated_at,
    conversations.c.stage,
    conversations.c.customer_waiting_since,
    conversations.c.ai_resumed_at,
)

# El hilo sin el contenido de los archivos: solo sus datos.
_ENTRY = (
    conversation_entries.c.id,
    conversation_entries.c.author,
    conversation_entries.c.body,
    conversation_entries.c.intent,
    conversation_entries.c.created_at,
    conversation_entries.c.kind,
    conversation_entries.c.status,
    conversation_entries.c.media_id,
    conversation_entries.c.media_note,
    conversation_entries.c.updated_at,
    conversation_media.c.mime_type,
    conversation_media.c.size_bytes,
    conversation_media.c.file_name,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: datetime | None) -> datetime | None:
    # SQLite devuelve fechas sin zona; todas se guardan en UTC.
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _summary(row: Any, now: datetime | None = None) -> ConversationSummary:
    typing_until = _utc(row.assistant_typing_until)
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
        handoff_reason=row.handoff_reason,
        handoff_summary=row.handoff_summary,
        ai_paused=bool(row.ai_paused),
        unread_count=int(row.unread_count or 0),
        assistant_typing=bool(typing_until and typing_until > (now or _now())),
        updated_at=_utc(row.updated_at),
        stage=row.stage or "new",
        customer_waiting_since=_utc(row.customer_waiting_since),
        ai_resumed_at=_utc(row.ai_resumed_at),
    )


def _message(row: Any) -> ChatMessage:
    media = MediaInfo(str(row.media_id), row.mime_type, int(row.size_bytes), row.file_name) if row.media_id and row.mime_type else None
    return ChatMessage(
        id=str(row.id),
        author=row.author,
        body=row.body,
        created_at=_utc(row.created_at),
        intent=row.intent,
        kind=row.kind or "text",
        status=row.status or "received",
        media=media,
        media_note=row.media_note,
        updated_at=_utc(row.updated_at),
    )


def _check(message: NewMessage) -> None:
    if message.author not in AUTHORS:
        raise ValueError("autor de mensaje desconocido")
    if message.kind not in KINDS:
        raise ValueError("tipo de mensaje desconocido")
    if message.resolved_status not in STATUSES:
        raise ValueError("estado de mensaje desconocido")


class ConversationStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------ guardar

    def record(
        self,
        tenant_slug: str,
        *,
        channel: str,
        contact_ref: str,
        contact_name: str | None,
        messages: list[NewMessage],
        handoff: bool = False,
        handoff_reason: str | None = None,
        handoff_summary: str | None = None,
    ) -> str:
        """Un intercambio completo (el área de pruebas): los mensajes en orden y, si trae el traspaso, el aviso al equipo."""
        if channel not in CHANNELS:
            raise ValueError(f"canal desconocido: {channel}")
        if not messages:
            raise ValueError("no hay mensajes para guardar")
        for message in messages:
            _check(message)
        for attempt in range(2):
            try:
                with self._engine.begin() as conn:
                    conversation_id, _paused = self._conversation(conn, tenant_slug, channel, contact_ref, contact_name)
                    now = _now()
                    for index, message in enumerate(messages):
                        # Un microsegundo entre mensajes del mismo intercambio: el hilo siempre conserva su orden.
                        self._insert_entry(conn, conversation_id, message, None, now + timedelta(microseconds=index))
                    self._touch(conn, conversation_id, messages, contact_name, now)
                    if handoff:
                        asked = next((message.body for message in messages if message.author == "customer"), None)
                        self._handoff(conn, conversation_id, handoff_reason or "human_request", asked, now, summary=handoff_summary)
                return str(conversation_id)
            except IntegrityError:
                # Otro proceso creó el mismo hilo a la vez: se repite y esta vez se encuentra.
                if attempt:
                    raise
        raise AssertionError("inalcanzable")

    def append(
        self,
        tenant_slug: str,
        *,
        channel: str,
        contact_ref: str,
        contact_name: str | None,
        message: NewMessage,
        media: MediaFile | None = None,
    ) -> AppendResult:
        """Un mensaje que llega o sale por un canal, apenas pasa. Un aviso repetido (mismo id del canal) no se guarda dos veces."""
        if channel not in CHANNELS:
            raise ValueError(f"canal desconocido: {channel}")
        _check(message)
        for attempt in range(2):
            try:
                with self._engine.begin() as conn:
                    conversation_id, paused = self._conversation(conn, tenant_slug, channel, contact_ref, contact_name)
                    if message.provider_message_id:
                        existing = conn.execute(
                            select(conversation_entries.c.id).where(
                                conversation_entries.c.conversation_id == conversation_id,
                                conversation_entries.c.provider_message_id == message.provider_message_id,
                            )
                        ).scalar_one_or_none()
                        if existing is not None:
                            return AppendResult(str(conversation_id), str(existing), False, paused)
                    now = _now()
                    media_id = self._insert_media(conn, conversation_id, media, now) if media is not None else None
                    entry_id = self._insert_entry(conn, conversation_id, message, media_id, now)
                    self._touch(conn, conversation_id, [message], contact_name, now)
                    return AppendResult(str(conversation_id), str(entry_id), True, paused)
            except IntegrityError:
                # El mismo hilo o el mismo mensaje entró a la vez por otro proceso: la segunda vez se encuentra.
                if attempt:
                    raise
        raise AssertionError("inalcanzable")

    def _conversation(self, conn: Connection, tenant_slug: str, channel: str, contact_ref: str, contact_name: str | None) -> tuple[uuid.UUID, bool]:
        tenant = tenant_of(conn, tenant_slug)
        key = and_(conversations.c.tenant_id == tenant.id, conversations.c.channel == channel, conversations.c.contact_ref == contact_ref)
        current = conn.execute(select(conversations.c.id, conversations.c.ai_paused).where(key)).first()
        if current is not None:
            return current.id, bool(current.ai_paused)
        conversation_id, now = uuid.uuid4(), _now()
        conn.execute(
            insert(conversations).values(
                id=conversation_id, tenant_id=tenant.id, channel=channel, contact_ref=contact_ref, contact_name=contact_name, status="open",
                started_at=now, last_message_at=now, message_count=0, needs_human=False, ai_paused=False, unread_count=0, updated_at=now,
            )
        )
        return conversation_id, False

    @staticmethod
    def _insert_entry(conn: Connection, conversation_id: uuid.UUID, message: NewMessage, media_id: uuid.UUID | None, at: datetime) -> uuid.UUID:
        entry_id = uuid.uuid4()
        conn.execute(
            insert(conversation_entries).values(
                id=entry_id, conversation_id=conversation_id, author=message.author, body=message.body, intent=message.intent,
                kind=message.kind, status=message.resolved_status, provider_message_id=message.provider_message_id, media_id=media_id,
                media_note=message.media_note, created_at=at, updated_at=at,
            )
        )
        return entry_id

    @staticmethod
    def _insert_media(conn: Connection, conversation_id: uuid.UUID, media: MediaFile, at: datetime) -> uuid.UUID:
        if len(media.content) > MAX_MEDIA_BYTES:
            raise ValueError("el archivo es más grande de lo que se guarda")
        tenant_id = conn.execute(select(conversations.c.tenant_id).where(conversations.c.id == conversation_id)).scalar_one()
        media_id = uuid.uuid4()
        conn.execute(
            insert(conversation_media).values(
                id=media_id, tenant_id=tenant_id, conversation_id=conversation_id, mime_type=media.mime_type, size_bytes=len(media.content),
                file_name=media.file_name, content=media.content, created_at=at,
            )
        )
        return media_id

    @staticmethod
    def _touch(conn: Connection, conversation_id: uuid.UUID, added: list[NewMessage], contact_name: str | None, now: datetime) -> None:
        last = added[-1]
        changes: dict[str, Any] = {
            "last_message_at": now,
            "last_message_preview": message_preview(last.kind, last.body),
            "message_count": conversations.c.message_count + len(added),
            "updated_at": now,
            **({"contact_name": contact_name} if contact_name else {}),
        }
        from_customer = sum(1 for message in added if message.author == "customer")
        if from_customer:
            changes["unread_count"] = conversations.c.unread_count + from_customer
            # Con la IA pausada, el cliente empieza a esperar a una persona desde su primer mensaje sin respuesta.
            state = conn.execute(
                select(conversations.c.ai_paused, conversations.c.customer_waiting_since).where(conversations.c.id == conversation_id)
            ).first()
            if state is not None and state.ai_paused and state.customer_waiting_since is None:
                changes["customer_waiting_since"] = now
        if any(message.author == "agent" for message in added):
            # Alguien del equipo respondió: el cliente ya no espera y el chat vuelve a ser del equipo.
            changes.update(customer_waiting_since=None, ai_resumed_at=None)
        # Lo que reconoció el asistente hace avanzar la etapa del cliente (nunca retrocede).
        reached = [stage for message in added if message.author == "assistant" for stage in [stage_for_intent(message.intent)] if stage]
        if reached:
            current = conn.execute(select(conversations.c.stage).where(conversations.c.id == conversation_id)).scalar_one()
            for stage in reached:
                current = advanced(current, stage) or current
            changes["stage"] = current
        conn.execute(update(conversations).where(conversations.c.id == conversation_id).values(**changes))

    def update_entry(
        self,
        entry_id: str,
        *,
        status: str | None = None,
        provider_message_id: str | None = None,
        media: MediaFile | None = None,
        media_note: str | None = None,
    ) -> None:
        """Completa un mensaje ya guardado: su estado e id del canal al salir, o el archivo y lo que la IA entendió de él."""
        if status is not None and status not in STATUSES:
            raise ValueError("estado de mensaje desconocido")
        key = self._key(entry_id)
        with self._engine.begin() as conn:
            conversation_id = conn.execute(select(conversation_entries.c.conversation_id).where(conversation_entries.c.id == key)).scalar_one_or_none()
            if conversation_id is None:
                raise ConversationNotFoundError("el mensaje no existe")
            now = _now()
            changes: dict[str, Any] = {"updated_at": now}
            if status is not None:
                changes["status"] = status
            if provider_message_id is not None:
                changes["provider_message_id"] = provider_message_id
            if media is not None:
                changes["media_id"] = self._insert_media(conn, conversation_id, media, now)
            if media_note is not None:
                changes["media_note"] = media_note
            conn.execute(update(conversation_entries).where(conversation_entries.c.id == key).values(**changes))
            conn.execute(update(conversations).where(conversations.c.id == conversation_id).values(updated_at=now))

    def mark_delivery(self, tenant_slug: str, provider_message_ids: Collection[str], status: str) -> int:
        """Los recibos del canal (entregado, leído) de lo que salió de ese negocio. Solo avanza; devuelve cuántos cambió."""
        ids = [str(item) for item in provider_message_ids if str(item or "").strip()][:100]
        if not ids or status not in STATUSES:
            return 0
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            rows = conn.execute(
                select(conversation_entries.c.id, conversation_entries.c.status, conversation_entries.c.conversation_id)
                .join(conversations, conversations.c.id == conversation_entries.c.conversation_id)
                .where(
                    conversations.c.tenant_id == tenant.id,
                    conversation_entries.c.provider_message_id.in_(ids),
                    conversation_entries.c.author != "customer",
                )
            ).all()
            now, changed = _now(), [row for row in rows if advances(row.status, status)]
            for row in changed:
                conn.execute(update(conversation_entries).where(conversation_entries.c.id == row.id).values(status=status, updated_at=now))
            for conversation_id in {row.conversation_id for row in changed}:
                conn.execute(update(conversations).where(conversations.c.id == conversation_id).values(updated_at=now))
        return len(changed)

    # ------------------------------------------------------------------ quién atiende

    def set_typing(self, conversation_id: str, until: datetime | None) -> None:
        """El asistente está «escribiendo…» hasta `until`; None lo apaga."""
        self._update(conversation_id, assistant_typing_until=until)

    def request_handoff(
        self, conversation_id: str, reason: str, detail: str | None = None, *, pause_ai: bool = True, summary: str | None = None
    ) -> str | None:
        """La conversación pasa a una persona: espera al equipo y, si no estaba esperando ya, se avisa al equipo. Con `pause_ai`
        (hay alguien del equipo en su horario) la IA se pausa y el cliente empieza a esperar; sin él (fuera del horario) la IA sigue
        ayudando mientras tanto. `summary` es la nota de la IA para el equipo (`handoff_brief.py`): va en el aviso y en el chat; sin
        ella, el aviso lleva lo último que escribió el cliente (`detail`). Devuelve el id del aviso nuevo, o None si ya estaba
        esperando."""
        with self._engine.begin() as conn:
            return self._handoff(conn, self._key(conversation_id), reason, detail, _now(), pause_ai=pause_ai, summary=summary)

    def _handoff(
        self,
        conn: Connection,
        conversation_id: uuid.UUID,
        reason: str,
        detail: str | None,
        now: datetime,
        *,
        pause_ai: bool = True,
        summary: str | None = None,
    ) -> str | None:
        reason = reason if reason in HANDOFF_REASONS else "assistant"
        row = conn.execute(
            select(
                conversations.c.tenant_id, conversations.c.channel, conversations.c.contact_name, conversations.c.needs_human,
                conversations.c.stage, conversations.c.ai_paused, conversations.c.customer_waiting_since, conversations.c.ai_resumed_at,
            ).where(conversations.c.id == conversation_id)
        ).first()
        if row is None:
            raise ConversationNotFoundError("la conversación no existe")
        # El área de pruebas no tiene a nadie del otro lado: se marca, pero la IA sigue respondiendo. Después de que la IA retomó sola
        # un chat que nadie atendió, tampoco se vuelve a pausar hasta que alguien del equipo lo atienda.
        pause = pause_ai and row.channel != "prueba" and row.ai_resumed_at is None
        # La nota de este paso (o ninguna): nunca queda la de un paso anterior.
        summary = " ".join(str(summary or "").split()) or None
        changes: dict[str, Any] = {"handoff_reason": reason, "handoff_summary": summary, "updated_at": now}
        if pause:
            changes["ai_paused"] = True
            if row.customer_waiting_since is None:
                changes["customer_waiting_since"] = now
        if reason == "payment_review" and advanced(row.stage, "payment"):
            changes["stage"] = "payment"
        notification_id = None
        if not row.needs_human:
            changes.update(needs_human=True, handoff_requested_at=now)
            notification_id = uuid.uuid4()
            conn.execute(
                insert(notifications).values(
                    id=notification_id, tenant_id=row.tenant_id, conversation_id=conversation_id, kind="handoff",
                    title=handoff_title(reason, row.channel, row.contact_name),
                    body=summary or (preview(detail) if detail else None),
                    created_at=now,
                )
            )
        conn.execute(update(conversations).where(conversations.c.id == conversation_id).values(**changes))
        return str(notification_id) if notification_id is not None else None

    def set_ai_paused(self, conversation_id: str, paused: bool) -> None:
        """Pausa o reanuda la IA en la conversación. Al reanudarla, la conversación deja de esperar a una persona. Pausarla a mano es
        tomar el chat: la IA ya no lo considera retomado por ella."""
        changes: dict[str, Any] = {"ai_paused": paused, "ai_resumed_at": None}
        if not paused:
            changes.update(needs_human=False, handoff_reason=None, handoff_summary=None, customer_waiting_since=None)
        self._update(conversation_id, **changes)

    def team_replied(self, conversation_id: str) -> None:
        """Alguien del equipo respondió por fuera del panel (desde el celular del negocio): el chat es suyo, la IA se pausa y el
        cliente deja de esperar."""
        self._update(conversation_id, ai_paused=True, needs_human=False, customer_waiting_since=None, ai_resumed_at=None)

    def stage_of(self, conversation_id: str) -> str:
        """La etapa a la que llegó el cliente de esa conversación."""
        with self._engine.connect() as conn:
            stage = conn.execute(select(conversations.c.stage).where(conversations.c.id == self._key(conversation_id))).scalar_one_or_none()
        if stage is None:
            raise ConversationNotFoundError("la conversación no existe")
        return stage

    def is_ai_paused(self, conversation_id: str) -> bool:
        with self._engine.connect() as conn:
            paused = conn.execute(select(conversations.c.ai_paused).where(conversations.c.id == self._key(conversation_id))).scalar_one_or_none()
        if paused is None:
            raise ConversationNotFoundError("la conversación no existe")
        return bool(paused)

    def resolve_handoff(self, conversation_id: str) -> None:
        """Alguien del equipo ya atendió a quien pidió una persona (desde aquí o desde su celular): el cliente deja de esperar."""
        self._update(conversation_id, needs_human=False, customer_waiting_since=None, ai_resumed_at=None)

    # ------------------------------------------------------------------ la IA retoma lo que nadie atendió

    def waiting_chats(self, *, waiting_before: datetime, limit: int = 100) -> list[WaitingChat]:
        """Los chats con la IA pausada y un cliente esperando desde antes de `waiting_before`, los más antiguos primero. Las pruebas
        nunca esperan (su IA no se pausa)."""
        query = (
            select(conversations.c.id, tenants.c.slug, conversations.c.channel, conversations.c.contact_ref, conversations.c.customer_waiting_since)
            .join(tenants, tenants.c.id == conversations.c.tenant_id)
            .where(
                conversations.c.ai_paused.is_(True),
                conversations.c.customer_waiting_since.is_not(None),
                conversations.c.customer_waiting_since <= waiting_before,
                conversations.c.channel.in_(RESUMABLE_CHANNELS),
            )
            .order_by(conversations.c.customer_waiting_since)
            .limit(limit)
        )
        with self._engine.connect() as conn:
            return [WaitingChat(str(row.id), row.slug, row.channel, row.contact_ref, _utc(row.customer_waiting_since)) for row in conn.execute(query)]

    def resume_waiting(self, conversation_id: str, *, waiting_before: datetime, minutes: int) -> str | None:
        """La IA retoma el chat si su cliente sigue esperando desde antes de `waiting_before`. Una sola vez: si otro proceso ya lo
        retomó o alguien del equipo respondió, no hace nada y devuelve None. Si lo retoma, avisa al equipo y devuelve el id del aviso.
        El chat sigue esperando a una persona (`needs_human`): la IA solo atiende mientras tanto."""
        key, now = self._key(conversation_id), _now()
        with self._engine.begin() as conn:
            claimed = conn.execute(
                update(conversations)
                .where(
                    conversations.c.id == key,
                    conversations.c.ai_paused.is_(True),
                    conversations.c.customer_waiting_since.is_not(None),
                    conversations.c.customer_waiting_since <= waiting_before,
                )
                .values(ai_paused=False, customer_waiting_since=None, ai_resumed_at=now, updated_at=now)
            ).rowcount
            if claimed != 1:
                return None
            row = conn.execute(select(conversations.c.tenant_id, conversations.c.contact_name).where(conversations.c.id == key)).one()
            notification_id = uuid.uuid4()
            conn.execute(
                insert(notifications).values(
                    id=notification_id, tenant_id=row.tenant_id, conversation_id=key, kind="ai_resumed",
                    title=f"La IA retomó el chat con {row.contact_name or 'un cliente'}",
                    body=f"Nadie le respondió en {minutes} minutos. El chat sigue esperando a alguien del equipo.", created_at=now,
                )
            )
        return str(notification_id)

    def pending_customer_text(self, conversation_id: str, *, since: datetime) -> str:
        """Lo que escribió el cliente desde `since` y nadie le respondió, en un solo texto (las fotos y audios, con lo que la IA
        entendió de ellos). Es lo que lee el asistente al retomar el chat."""
        query = (
            select(conversation_entries.c.body, conversation_entries.c.kind, conversation_entries.c.media_note)
            .where(
                conversation_entries.c.conversation_id == self._key(conversation_id),
                conversation_entries.c.author == "customer",
                conversation_entries.c.created_at >= since,
            )
            .order_by(conversation_entries.c.created_at)
        )
        with self._engine.connect() as conn:
            rows = conn.execute(query).all()
        lines = []
        for row in rows:
            text = str(row.body or "").strip()
            if row.kind != "text" and row.media_note:
                text = f"{text} [{row.media_note}]".strip()
            if text:
                lines.append(text)
        return "\n".join(lines)

    def mark_read(self, conversation_id: str) -> None:
        """Alguien del equipo abrió la conversación: no quedan mensajes sin leer."""
        self._update(conversation_id, unread_count=0)

    # ------------------------------------------------------------------ borrar

    def delete(self, conversation_id: str) -> ConversationTarget:
        """Borra la conversación con todo lo suyo: mensajes, fotos, audios y documentos, y sus avisos. Las ventas registradas se
        conservan sin el enlace al chat (la base las deja en `NULL`): son la contabilidad del negocio. Devuelve de quién era."""
        target = self.target(conversation_id)
        with self._engine.begin() as conn:
            conn.execute(delete(conversations).where(conversations.c.id == self._key(conversation_id)))
        return target

    def delete_channel(self, tenant_slug: str, channel: str) -> int:
        """Borra todas las conversaciones de un canal de ese negocio (por ejemplo, las de «Probar asistente») y dice cuántas eran."""
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            result = conn.execute(delete(conversations).where(conversations.c.tenant_id == tenant.id, conversations.c.channel == channel))
        return int(result.rowcount or 0)

    def _update(self, conversation_id: str, **values: Any) -> None:
        with self._engine.begin() as conn:
            result = conn.execute(update(conversations).where(conversations.c.id == self._key(conversation_id)).values(updated_at=_now(), **values))
        if result.rowcount == 0:
            raise ConversationNotFoundError("la conversación no existe")

    # ------------------------------------------------------------------ leer

    def recent(self, tenant_slugs: Collection[str], *, channel: str | None, limit: int, needs_human: bool | None = None) -> list[ConversationSummary]:
        query = select(*_SUMMARY).join(tenants, tenants.c.id == conversations.c.tenant_id).where(tenants.c.slug.in_(list(tenant_slugs)))
        if channel is not None:
            query = query.where(conversations.c.channel == channel)
        if needs_human is not None:
            query = query.where(conversations.c.needs_human.is_(needs_human))
        query = query.order_by(conversations.c.last_message_at.desc()).limit(limit)
        now = _now()
        with self._engine.connect() as conn:
            return [_summary(row, now) for row in conn.execute(query)]

    def _key(self, identifier: str) -> uuid.UUID:
        try:
            return uuid.UUID(str(identifier))
        except ValueError as exc:
            raise ConversationNotFoundError("identificador no válido") from exc

    def _summary_of(self, conn: Connection, key: uuid.UUID) -> ConversationSummary:
        row = conn.execute(select(*_SUMMARY).join(tenants, tenants.c.id == conversations.c.tenant_id).where(conversations.c.id == key)).first()
        if row is None:
            raise ConversationNotFoundError("la conversación no existe")
        return _summary(row)

    def _entries(self, conn: Connection, key: uuid.UUID, since: datetime | None = None) -> list[ChatMessage]:
        query = (
            select(*_ENTRY)
            .select_from(conversation_entries.outerjoin(conversation_media, conversation_media.c.id == conversation_entries.c.media_id))
            .where(conversation_entries.c.conversation_id == key)
        )
        if since is not None:
            query = query.where(conversation_entries.c.updated_at >= since - LIVE_OVERLAP)
        return [_message(row) for row in conn.execute(query.order_by(conversation_entries.c.created_at))]

    def thread(self, conversation_id: str) -> tuple[ConversationSummary, list[ChatMessage]]:
        key = self._key(conversation_id)
        with self._engine.connect() as conn:
            return self._summary_of(conn, key), self._entries(conn, key)

    def changes(self, conversation_id: str, since: datetime | None) -> tuple[ConversationSummary, list[ChatMessage]]:
        """La conversación y los mensajes nuevos o que cambiaron desde `since` (sin `since`, todos)."""
        key = self._key(conversation_id)
        with self._engine.connect() as conn:
            return self._summary_of(conn, key), self._entries(conn, key, since)

    def business_of(self, conversation_id: str) -> str:
        """El negocio de la conversación, para comprobar el acceso antes de cambiarla."""
        return self.target(conversation_id).business_slug

    def target(self, conversation_id: str) -> ConversationTarget:
        key = self._key(conversation_id)
        with self._engine.connect() as conn:
            row = conn.execute(
                select(tenants.c.slug, conversations.c.channel, conversations.c.contact_ref)
                .join(conversations, conversations.c.tenant_id == tenants.c.id)
                .where(conversations.c.id == key)
            ).first()
        if row is None:
            raise ConversationNotFoundError("la conversación no existe")
        return ConversationTarget(row.slug, row.channel, row.contact_ref)

    def media(self, conversation_id: str, media_id: str) -> MediaFile:
        """Un archivo de la conversación, solo si es de esa conversación."""
        with self._engine.connect() as conn:
            row = conn.execute(
                select(conversation_media.c.mime_type, conversation_media.c.content, conversation_media.c.file_name).where(
                    conversation_media.c.id == self._key(media_id), conversation_media.c.conversation_id == self._key(conversation_id)
                )
            ).first()
        if row is None:
            raise ConversationNotFoundError("el archivo no existe")
        return MediaFile(row.mime_type, bytes(row.content), row.file_name)

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
