"""La API del asistente (Integraciones → API / HTTP): otro sistema le manda el mensaje de un cliente y recibe la respuesta.

Es el mismo asistente que atiende WhatsApp: responde con lo publicado del negocio, recuerda a cada cliente, pasa a una persona
según el horario del equipo y gasta la clave de IA del negocio. Lo que cambia es quién entrega la respuesta: la API solo la
devuelve, y el sistema que llamó (Leona, una web...) se la envía al cliente. Por eso, cuando el chat pasa a una persona, la API
responde `handoff: true` y ese sistema decide quién atiende.

Aquí está el formato, sin red ni base de datos. Acepta lo que mandan las plataformas de automatización (como Leona), que suelen
armar el cuerpo con variables: el contacto como objeto o como campos sueltos, y el mensaje como texto o como objeto.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError

API_CHANNEL = "api"
MAX_CONTACT_ID_CHARS = 120
MAX_CONTACT_NAME_CHARS = 120
MAX_MESSAGE_CHARS = 4000
MAX_IDEMPOTENCY_KEY_CHARS = 128


@dataclass(frozen=True)
class ApiMessage:
    """Un mensaje de un cliente que llega por la API."""

    contact_id: str
    text: str
    contact_name: str | None = None


@dataclass(frozen=True)
class ApiReply:
    """Lo que devuelve la API. `reply` es todo lo que hay que enviarle al cliente (vacío si lo atiende el equipo); `parts`, lo
    mismo en mensajes separados, para quien prefiera enviarlos uno por uno."""

    conversation_id: str
    reply: str
    parts: tuple[str, ...] = ()
    # El chat necesita a una persona: el sistema que llamó debe pasarlo a su equipo.
    handoff: bool = False
    handoff_reason: str | None = None
    # Quién atiende ahora: `assistant`, o `team` si el chat lo lleva una persona (la IA no respondió).
    attended_by: str = "assistant"
    intent: str | None = None
    stage: str = "new"
    # Respondió con el mensaje de respaldo del negocio porque la IA no pudo (sin clave, sin saldo, proveedor caído).
    fallback: bool = False
    # El mismo pedido ya se había respondido (misma `Idempotency-Key`): es esa misma respuesta.
    duplicate: bool = False


def _text(value: Any) -> str:
    return str(value).strip() if isinstance(value, (str, int, float)) and not isinstance(value, bool) else ""


def parse_message(payload: Any) -> ApiMessage:
    """El cuerpo de la petición, revisado. Acepta `{"contact": {"id", "name"}, "message": "..."}` y también los campos sueltos
    `contact_id`, `contact_name`, `phone` y `message: {"text": "..."}`."""
    if not isinstance(payload, dict):
        raise InvalidFieldsError("El cuerpo debe ser un objeto JSON.", [FieldIssue("body", "Envía un objeto JSON.")])
    contact = payload.get("contact") if isinstance(payload.get("contact"), dict) else {}
    contact_id = _text(contact.get("id")) or _text(contact.get("phone")) or _text(payload.get("contact_id")) or _text(payload.get("phone"))
    name = _text(contact.get("name")) or _text(payload.get("contact_name")) or None
    raw_message = payload.get("message")
    text = _text(raw_message.get("text")) if isinstance(raw_message, dict) else _text(raw_message)
    issues: list[FieldIssue] = []
    if not contact_id or len(contact_id) > MAX_CONTACT_ID_CHARS:
        issues.append(FieldIssue("contact.id", f"Envía el identificador del cliente (su teléfono o su id), de hasta {MAX_CONTACT_ID_CHARS} caracteres."))
    if not text:
        issues.append(FieldIssue("message", "Envía el mensaje del cliente."))
    elif len(text) > MAX_MESSAGE_CHARS:
        issues.append(FieldIssue("message", f"El mensaje puede tener hasta {MAX_MESSAGE_CHARS} caracteres."))
    if name is not None and len(name) > MAX_CONTACT_NAME_CHARS:
        issues.append(FieldIssue("contact.name", f"El nombre puede tener hasta {MAX_CONTACT_NAME_CHARS} caracteres."))
    if issues:
        raise InvalidFieldsError("Revisa la petición.", issues)
    return ApiMessage(contact_id=contact_id, text=text, contact_name=name)


def valid_idempotency_key(value: str | None) -> str | None:
    key = str(value or "").strip()
    if not key:
        return None
    if len(key) > MAX_IDEMPOTENCY_KEY_CHARS or not key.isprintable():
        raise InvalidFieldsError("Revisa la petición.", [FieldIssue("Idempotency-Key", f"Hasta {MAX_IDEMPOTENCY_KEY_CHARS} caracteres visibles.")])
    return key


def reply_payload(result: ApiReply) -> dict[str, Any]:
    """La respuesta JSON de la API (estable: lo que documenta `docs/api.md`)."""
    return {
        "conversation_id": result.conversation_id,
        "reply": result.reply,
        "parts": list(result.parts),
        "handoff": result.handoff,
        "handoff_reason": result.handoff_reason,
        "attended_by": result.attended_by,
        "intent": result.intent,
        "stage": result.stage,
        "fallback": result.fallback,
        "duplicate": result.duplicate,
    }


def reply_from_payload(payload: dict[str, Any]) -> ApiReply:
    """Una respuesta guardada (la de `reply_payload`), otra vez como `ApiReply`."""
    return ApiReply(
        conversation_id=str(payload.get("conversation_id") or ""),
        reply=str(payload.get("reply") or ""),
        parts=tuple(str(part) for part in payload.get("parts") or ()),
        handoff=bool(payload.get("handoff")),
        handoff_reason=payload.get("handoff_reason"),
        attended_by=str(payload.get("attended_by") or "assistant"),
        intent=payload.get("intent"),
        stage=str(payload.get("stage") or "new"),
        fallback=bool(payload.get("fallback")),
        duplicate=bool(payload.get("duplicate")),
    )
