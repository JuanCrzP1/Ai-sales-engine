"""La bandeja de conversaciones del panel: los chats de los negocios de cada usuario, de todos sus canales.

Cada usuario solo ve las conversaciones de sus negocios (`BusinessAccess`). Una conversación ajena responde igual que una
inexistente. También registra las conversaciones del área de pruebas, con el canal `prueba` y los datos de pago ocultos.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import ConversationStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.conversations import CHANNELS, MAX_PAGE, BusinessActivity, ChatMessage, ConversationSummary, NewMessage
from app.domain.business_config.errors import BusinessNotFoundError, ConversationNotFoundError, FieldIssue, InvalidFieldsError
from app.domain.business_config.payment_data import redact_payment_values

logger = logging.getLogger("conversations")

_CONVERSATION_ID = re.compile(r"[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
PLAYGROUND_CHANNEL = "prueba"
PLAYGROUND_CONTACT = "Prueba en el panel"


class ConversationsService:
    def __init__(self, storage: ConversationStorage, access: BusinessAccess) -> None:
        self._storage = storage
        self._access = access

    def inbox(self, principal: Principal, *, business: str | None = None, channel: str | None = None, limit: int = 50) -> list[ConversationSummary]:
        """Lo más reciente primero, de un negocio o de todos los del usuario."""
        mine = {summary.slug for summary in self._access.list_for(principal)}
        if business is not None:
            if business not in mine:
                raise BusinessNotFoundError(f"{business}: no existe o no pertenece a este usuario")
            mine = {business}
        if channel is not None and channel not in CHANNELS:
            raise InvalidFieldsError("Revisa el filtro.", [FieldIssue("channel", "Ese canal no existe.")])
        if not mine:
            return []
        return self._storage.recent(mine, channel=channel, limit=max(1, min(limit, MAX_PAGE)))

    def thread(self, principal: Principal, conversation_id: str) -> tuple[ConversationSummary, list[ChatMessage]]:
        if not _CONVERSATION_ID.fullmatch(str(conversation_id or "").lower()):
            raise ConversationNotFoundError("identificador no válido")
        summary, messages = self._storage.thread(conversation_id)
        try:
            self._access.require(principal, summary.business_slug)
        except BusinessNotFoundError as exc:
            raise ConversationNotFoundError("la conversación no existe o es de otro usuario") from exc
        return summary, messages

    def activity(self, principal: Principal, business: str, *, now: datetime | None = None) -> BusinessActivity:
        self._access.require(principal, business)
        today = (now or datetime.now(timezone.utc)).replace(hour=0, minute=0, second=0, microsecond=0)
        return self._storage.activity(business, since=today)


class PlaygroundRecorder:
    """Guarda cada intercambio del área de pruebas en la bandeja, con los datos de pago ocultos. Si falla, la prueba sigue."""

    def __init__(self, storage: ConversationStorage) -> None:
        self._storage = storage

    def record(self, tenant_slug: str, *, session_id: str, sections: dict[str, dict], message: str, reply: str, intent: str | None) -> None:
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
            )
        except Exception:  # noqa: BLE001 - la bandeja no puede tumbar la prueba; se registra el tipo, nunca el contenido
            logger.exception("conversacion_de_prueba_no_guardada")
