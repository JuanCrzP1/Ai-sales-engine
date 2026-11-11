"""La bandeja de conversaciones del panel: los chats de los negocios de cada usuario, de todos sus canales, en vivo.

Cada usuario solo ve las conversaciones de sus negocios (`BusinessAccess`). Una conversación ajena responde igual que una
inexistente. El panel pide solo lo que cambió desde su última marca (`live`), y el equipo puede responder desde aquí: el mensaje
sale por el canal del cliente y la IA se pausa en ese chat, porque la conversación ya la lleva una persona, hasta que la reanuden.
También registra las conversaciones del área de pruebas, con el canal `prueba` y los datos de pago ocultos.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import ConversationStorage, NotificationStorage, OutboundMessenger
from app.domain.business_config.access import Principal
from app.domain.business_config.channels import ChannelError
from app.domain.business_config.conversations import (
    CHANNELS,
    MAX_PAGE,
    MAX_REPLY_CHARS,
    REPLYABLE_CHANNELS,
    BusinessActivity,
    ChatMessage,
    ConversationSummary,
    MediaFile,
    NewMessage,
    Notification,
)
from app.domain.business_config.errors import BusinessNotFoundError, ConversationNotFoundError, FieldIssue, InvalidFieldsError
from app.domain.business_config.payment_data import redact_payment_values

logger = logging.getLogger("conversations")

_CONVERSATION_ID = re.compile(r"[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
PLAYGROUND_CHANNEL = "prueba"
PLAYGROUND_CONTACT = "Prueba en el panel"


class ReplyNotSentError(RuntimeError):
    """La respuesta del equipo quedó guardada, pero el canal no la entregó. El mensaje es para el negocio."""


class ConversationsService:
    def __init__(self, storage: ConversationStorage, access: BusinessAccess, messenger: OutboundMessenger | None = None) -> None:
        self._storage = storage
        self._access = access
        self._messenger = messenger

    def _require(self, principal: Principal, conversation_id: str) -> str:
        """El negocio de la conversación, si es de quien pregunta; si no, como si no existiera."""
        if not _CONVERSATION_ID.fullmatch(str(conversation_id or "").lower()):
            raise ConversationNotFoundError("identificador no válido")
        try:
            business = self._storage.business_of(conversation_id)
            self._access.require(principal, business)
        except BusinessNotFoundError as exc:
            raise ConversationNotFoundError("la conversación no existe o es de otro usuario") from exc
        return business

    def inbox(
        self, principal: Principal, *, business: str | None = None, channel: str | None = None, waiting_human: bool = False, limit: int = 50
    ) -> list[ConversationSummary]:
        """Lo más reciente primero, de un negocio o de todos los del usuario. Con `waiting_human`, solo las que esperan a una persona."""
        mine = {summary.slug for summary in self._access.list_for(principal)}
        if business is not None:
            if business not in mine:
                raise BusinessNotFoundError(f"{business}: no existe o no pertenece a este usuario")
            mine = {business}
        if channel is not None and channel not in CHANNELS:
            raise InvalidFieldsError("Revisa el filtro.", [FieldIssue("channel", "Ese canal no existe.")])
        if not mine:
            return []
        return self._storage.recent(mine, channel=channel, limit=max(1, min(limit, MAX_PAGE)), needs_human=True if waiting_human else None)

    def thread(self, principal: Principal, conversation_id: str) -> tuple[ConversationSummary, list[ChatMessage]]:
        if not _CONVERSATION_ID.fullmatch(str(conversation_id or "").lower()):
            raise ConversationNotFoundError("identificador no válido")
        summary, messages = self._storage.thread(conversation_id)
        try:
            self._access.require(principal, summary.business_slug)
        except BusinessNotFoundError as exc:
            raise ConversationNotFoundError("la conversación no existe o es de otro usuario") from exc
        return summary, messages

    def live(self, principal: Principal, conversation_id: str, since: datetime | None) -> tuple[ConversationSummary, list[ChatMessage]]:
        """La conversación y los mensajes nuevos o que cambiaron desde `since` (sin `since`, todos)."""
        self._require(principal, conversation_id)
        return self._storage.changes(conversation_id, since)

    def resolve_handoff(self, principal: Principal, conversation_id: str) -> ConversationSummary:
        """Alguien del equipo ya atendió a quien pidió una persona: la conversación deja de esperar."""
        self._require(principal, conversation_id)
        self._storage.resolve_handoff(conversation_id)
        return self._storage.thread(conversation_id)[0]

    def set_assistant(self, principal: Principal, conversation_id: str, *, active: bool) -> ConversationSummary:
        """Reanuda la IA en la conversación (deja de esperar a una persona) o la pausa para atenderla el equipo."""
        self._require(principal, conversation_id)
        self._storage.set_ai_paused(conversation_id, not active)
        return self._storage.thread(conversation_id)[0]

    def mark_read(self, principal: Principal, conversation_id: str) -> None:
        self._require(principal, conversation_id)
        self._storage.mark_read(conversation_id)

    def media(self, principal: Principal, conversation_id: str, media_id: str) -> MediaFile:
        self._require(principal, conversation_id)
        return self._storage.media(conversation_id, media_id)

    def reply(self, principal: Principal, conversation_id: str, text: str) -> ChatMessage:
        """El equipo responde desde el panel: el mensaje se guarda enseguida («enviando»), sale por el canal del cliente y la IA se
        pausa en ese chat. Si el canal no lo entrega, queda «no enviado» y se informa."""
        self._require(principal, conversation_id)
        body = str(text or "").strip()
        if not body:
            raise InvalidFieldsError("Escribe la respuesta.", [FieldIssue("text", "Escribe la respuesta.")])
        if len(body) > MAX_REPLY_CHARS:
            raise InvalidFieldsError("La respuesta es muy larga.", [FieldIssue("text", f"Máximo {MAX_REPLY_CHARS} caracteres.")])
        target = self._storage.target(conversation_id)
        if target.channel not in REPLYABLE_CHANNELS or self._messenger is None:
            raise InvalidFieldsError(
                "Desde aquí todavía no se puede responder por este canal.", [FieldIssue("text", "Este canal no permite responder desde el panel.")]
            )
        saved = self._storage.append(
            target.business_slug, channel=target.channel, contact_ref=target.contact_ref, contact_name=None,
            message=NewMessage("agent", body, status="sending"),
        )
        # La conversación ya la lleva una persona: la IA no responde encima de ella.
        self._storage.set_ai_paused(conversation_id, True)
        self._storage.resolve_handoff(conversation_id)
        try:
            provider_id = self._messenger.send_text(target.business_slug, target.channel, target.contact_ref, body)
        except ChannelError as exc:
            self._storage.update_entry(saved.entry_id, status="failed")
            raise ReplyNotSentError(str(exc)) from exc
        self._storage.update_entry(saved.entry_id, status="sent", provider_message_id=provider_id)
        return next(message for message in self._storage.thread(conversation_id)[1] if message.id == saved.entry_id)

    def activity(self, principal: Principal, business: str, *, now: datetime | None = None) -> BusinessActivity:
        self._access.require(principal, business)
        today = (now or datetime.now(timezone.utc)).replace(hour=0, minute=0, second=0, microsecond=0)
        return self._storage.activity(business, since=today)


class NotificationsService:
    """Los avisos de los negocios del usuario (por ahora, cuando el asistente pasa una conversación a una persona)."""

    def __init__(self, storage: NotificationStorage, access: BusinessAccess) -> None:
        self._storage = storage
        self._access = access

    def _mine(self, principal: Principal) -> set[str]:
        return {summary.slug for summary in self._access.list_for(principal)}

    def recent(self, principal: Principal, *, limit: int = 20) -> tuple[list[Notification], int]:
        mine = self._mine(principal)
        return self._storage.recent(mine, principal.user_id, limit=max(1, min(limit, MAX_PAGE))) if mine else ([], 0)

    def mark_read(self, principal: Principal, ids: list[str] | None = None) -> int:
        mine = self._mine(principal)
        return self._storage.mark_read(mine, principal.user_id, ids) if mine else 0


class PlaygroundRecorder:
    """Guarda cada intercambio del área de pruebas en la bandeja, con los datos de pago ocultos. Si falla, la prueba sigue."""

    def __init__(self, storage: ConversationStorage) -> None:
        self._storage = storage

    def record(
        self,
        tenant_slug: str,
        *,
        session_id: str,
        sections: dict[str, dict],
        message: str,
        reply: str,
        intent: str | None,
        handoff: bool = False,
        handoff_reason: str | None = None,
    ) -> None:
        try:
            self._storage.record(
                tenant_slug,
                channel=PLAYGROUND_CHANNEL,
                contact_ref=session_id,
                contact_name=PLAYGROUND_CONTACT,
                messages=[
                    NewMessage("customer", redact_payment_values(message, sections)),
                    NewMessage("assistant", redact_payment_values(reply, sections), intent),
                ],
                handoff=handoff,
                handoff_reason=handoff_reason,
            )
        except Exception:  # noqa: BLE001 - la bandeja no puede tumbar la prueba; se registra el tipo, nunca el contenido
            logger.exception("conversacion_de_prueba_no_guardada")
