"""La API del asistente, de punta a punta: otro sistema (Leona, una web) manda el mensaje de un cliente y recibe la respuesta.

Es el mismo asistente de WhatsApp, con las mismas reglas, en el canal `api`:
1. Si llega con una `Idempotency-Key` ya respondida (24 horas), se devuelve exactamente esa respuesta, sin gastar la IA ni repetir
   nada. Si el mismo pedido todavía se está respondiendo, se avisa (`DuplicateInProgressError`). Si no, el mensaje del cliente se
   guarda en la bandeja apenas llega (con los datos de pago ocultos).
2. Si el chat lo atiende una persona (la IA está pausada), no responde: devuelve `attended_by: team`.
3. Si no, responde el asistente con lo publicado del negocio, su memoria de ese cliente y su clave de IA.
4. Si el chat necesita a una persona, pasa al equipo según su horario (la misma regla de WhatsApp, `handoff_plan.py`): se avisa
   al equipo (campana, correo, notificación) y la respuesta dice `handoff: true`, con el aviso de espera si corresponde.

La respuesta sale completa para el cliente (con sus datos de pago), y en la bandeja queda con ellos ocultos. Nunca envía nada por
su cuenta: entregarla es del sistema que llamó.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Protocol

from app.application.channels.handoff_plan import AttentionLoader, SectionsLoader, plan_handoff
from app.domain.business_config.assistant_api import API_CHANNEL, ApiMessage, ApiReply, reply_from_payload, reply_payload
from app.domain.business_config.conversations import AppendResult, NewMessage
from app.domain.business_config.payment_data import redact_payment_values
from app.utils.logger import logger


class ApiConversationGateway(Protocol):
    """La bandeja, vista desde el motor (`runtime_access`)."""

    def append(self, tenant_slug: str, *, channel: str, contact_ref: str, contact_name: str | None, message: NewMessage, media: Any = None) -> AppendResult: ...

    def request_handoff(
        self, conversation_id: str, reason: str, detail: str | None = None, *, pause_ai: bool = True, summary: str | None = None
    ) -> str | None: ...

    def ai_paused(self, conversation_id: str) -> bool: ...

    def stage(self, conversation_id: str) -> str: ...


class IdempotencyCache(Protocol):
    """Las respuestas ya dadas a cada `Idempotency-Key`, cifradas (`idempotency_store.py`)."""

    def get(self, tenant_slug: str, idempotency_key: str) -> dict[str, Any] | None: ...

    def put(self, tenant_slug: str, idempotency_key: str, response: dict[str, Any]) -> None: ...


class DuplicateInProgressError(RuntimeError):
    """El mismo pedido (misma `Idempotency-Key`) se está respondiendo en este momento."""


# El asistente del negocio: (negocio, cliente, texto) → (respuesta, si respondió la IA, metadatos: intent, handoff, handoff_reason).
ApiResponder = Callable[[str, str, str], tuple[str, bool, dict]]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AssistantApi:
    def __init__(
        self,
        *,
        conversations: ApiConversationGateway,
        responder: ApiResponder,
        attention: AttentionLoader,
        sections: SectionsLoader,
        alerts: Callable[[str | None], Any] | None = None,
        idempotency: IdempotencyCache | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._conversations = conversations
        self._responder = responder
        self._attention = attention
        self._sections = sections
        self._alerts = alerts or (lambda _notification: None)
        self._idempotency = idempotency
        self._clock = clock or _now

    def reply(self, slug: str, message: ApiMessage, *, idempotency_key: str | None = None) -> ApiReply:
        if idempotency_key and self._idempotency is not None:
            previous = self._idempotency.get(slug, idempotency_key)
            if previous is not None:
                return replace(reply_from_payload(previous), duplicate=True)
        stored = self._conversations.append(
            slug, channel=API_CHANNEL, contact_ref=message.contact_id, contact_name=message.contact_name,
            message=NewMessage("customer", self._hide(slug, message.text), provider_message_id=idempotency_key),
        )
        if not stored.created:
            # El mismo pedido llegó dos veces a la vez: el primero lo está respondiendo.
            raise DuplicateInProgressError("ese pedido ya se está respondiendo")
        result = self._answer(slug, message, stored)
        if idempotency_key and self._idempotency is not None:
            self._idempotency.put(slug, idempotency_key, reply_payload(result))
        return result

    def _answer(self, slug: str, message: ApiMessage, stored: AppendResult) -> ApiReply:
        conversation = stored.conversation_id
        if stored.ai_paused:
            return self._team(conversation)

        reply, ai_used, metadata = self._responder(slug, message.contact_id, message.text)
        reply = str(reply or "").strip()
        # Mientras el asistente pensaba, alguien del equipo pudo tomar el chat: entonces no responde.
        if self._conversations.ai_paused(conversation):
            logger.info("api_respuesta_descartada", extra={"tenant": slug, "reason": "chat_tomado_por_el_equipo"})
            return self._team(conversation)
        intent = str(metadata.get("intent") or "").strip() or None
        parts: list[str] = []
        if reply:
            self._record(slug, message, reply, intent)
            parts.append(reply)

        handoff, reason, attended_by = bool(metadata.get("handoff")), None, "assistant"
        if handoff:
            reason = str(metadata.get("handoff_reason") or "assistant")
            plan = plan_handoff(slug, attention=self._attention, sections=self._sections, now=self._clock())
            summary = str(metadata.get("handoff_summary") or "")
            notification = self._conversations.request_handoff(
                conversation, reason, self._hide(slug, message.text), pause_ai=plan.pause_ai, summary=self._hide(slug, summary) if summary else None
            )
            if plan.notice:
                self._record(slug, message, plan.notice, None)
                parts.append(plan.notice)
            attended_by = "team" if plan.pause_ai else "assistant"
            self._alerts(notification)
        logger.info("api_respuesta", extra={"tenant": slug, "handoff": handoff, "ai": bool(ai_used)})
        return ApiReply(
            conversation, "\n\n".join(parts), tuple(parts), handoff=handoff, handoff_reason=reason, attended_by=attended_by, intent=intent,
            stage=self._conversations.stage(conversation), fallback=not ai_used,
        )

    def _team(self, conversation: str) -> ApiReply:
        return ApiReply(conversation, "", (), handoff=True, attended_by="team", stage=self._conversations.stage(conversation))

    def _record(self, slug: str, message: ApiMessage, text: str, intent: str | None) -> None:
        self._conversations.append(
            slug, channel=API_CHANNEL, contact_ref=message.contact_id, contact_name=None,
            message=NewMessage("assistant", self._hide(slug, text), intent, status="sent"),
        )

    def _hide(self, slug: str, text: str) -> str:
        if not text:
            return text
        try:
            sections = self._sections(slug)
        except Exception:  # noqa: BLE001 - sin lo publicado no hay datos de pago que ocultar
            sections = {}
        return redact_payment_values(text, sections)
