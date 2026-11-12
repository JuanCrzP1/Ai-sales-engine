"""`POST /api/v1/assistant/messages`: la API del asistente (Integraciones → API / HTTP).

Otro sistema (Leona, una web, un servidor propio) manda el mensaje de un cliente con una clave de API del negocio y recibe la
respuesta del asistente. La referencia para quien la integra está en `docs/api.md`; el flujo, en
`app/application/channels/assistant_api.py`.

- Autenticación: `Authorization: Bearer ase_live_…` (una clave con el permiso «Conversar con el asistente»). Sin ella, 401; sin
  el permiso, 403. La clave decide el negocio: no se elige en la petición.
- Límites: 60 mensajes por minuto por clave y 1.500 por hora por negocio (429 con `Retry-After`).
- `Idempotency-Key` (opcional): el mismo pedido repetido devuelve la misma respuesta durante 24 horas, sin volver a gastar la IA
  (409 si el primero todavía se está respondiendo).
- Los errores siempre llegan como `{"code", "message", "issues"}`, igual que la API del panel.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.api.controllers.team_alerts import deliver_alert
from app.application.channels.assistant_api import AssistantApi, DuplicateInProgressError
from app.application.runtime import published_sections
from app.domain.business_config.api_keys import SCOPE_ASSISTANT_CHAT
from app.domain.business_config.assistant_api import parse_message, reply_payload, valid_idempotency_key
from app.domain.business_config.errors import InvalidFieldsError, UsageLimitExceededError
from app.infrastructure.business_config import runtime_access
from app.models import Tenant
from app.services.ai_service import AIService
from app.utils.logger import logger

router = APIRouter(prefix="/assistant", tags=["API del asistente"])


def answer(slug: str, contact_id: str, text: str) -> tuple[str, bool, dict]:
    """El asistente del negocio, con lo publicado y su clave de IA; la memoria de cada cliente la guarda el motor."""
    reply, ai_used, metadata = AIService().generate_business_reply(
        tenant=Tenant(name=slug, slug=slug),
        bot_config=None,
        user_message=text,
        user_id=contact_id,
        conversation_history=[],
        faq_results=[],
        yaml_config=None,
        include_metadata=True,
    )
    return str(reply or ""), bool(ai_used), metadata if isinstance(metadata, dict) else {}


class _Conversations:
    """La bandeja vista desde el motor: `runtime_access`, su única puerta al almacén."""

    append = staticmethod(runtime_access.append_conversation_message)
    request_handoff = staticmethod(runtime_access.request_conversation_handoff)
    ai_paused = staticmethod(runtime_access.conversation_ai_paused)
    stage = staticmethod(runtime_access.conversation_stage)


def build_assistant_api() -> AssistantApi:
    return AssistantApi(
        conversations=_Conversations(),
        responder=answer,
        attention=runtime_access.attention_settings,
        sections=published_sections,
        alerts=deliver_alert,
        idempotency=runtime_access.idempotency_store(),
    )


def _error(status_code: int, code: str, message: str, issues: list[dict[str, str]] | None = None, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse({"code": code, "message": message, "issues": issues or []}, status_code, headers=headers)


@router.post("/messages")
async def assistant_message(request: Request) -> Any:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    identity = runtime_access.authenticate_api_key(token.strip()) if scheme.lower() == "bearer" else None
    if identity is None:
        return _error(status.HTTP_401_UNAUTHORIZED, "invalid_api_key", "La clave de API no es válida o fue revocada.", headers={"WWW-Authenticate": "Bearer"})
    if SCOPE_ASSISTANT_CHAT not in identity.scopes:
        return _error(status.HTTP_403_FORBIDDEN, "forbidden", "Esta clave no tiene permiso para conversar con el asistente.")
    try:
        runtime_access.usage_guard().assistant_api(identity.key_id, identity.business_slug)
    except UsageLimitExceededError as exc:
        return _error(
            status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited", "Demasiados mensajes seguidos. Espera un momento y vuelve a intentarlo.",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        )
    try:
        payload = await request.json()
    except ValueError:
        return _error(status.HTTP_400_BAD_REQUEST, "invalid_json", "El cuerpo no es un JSON válido.")
    try:
        message = parse_message(payload)
        idempotency_key = valid_idempotency_key(request.headers.get("idempotency-key"))
    except InvalidFieldsError as exc:
        return _error(422, "invalid", str(exc), [{"path": issue.path, "message": issue.message} for issue in exc.issues])
    try:
        result = await run_in_threadpool(build_assistant_api().reply, identity.business_slug, message, idempotency_key=idempotency_key)
    except DuplicateInProgressError:
        return _error(status.HTTP_409_CONFLICT, "duplicate_in_progress", "Ese mismo pedido se está respondiendo. Vuelve a intentarlo en unos segundos.")
    except Exception as exc:  # noqa: BLE001 - sin detalles internos en la respuesta; queda el tipo en el registro
        logger.error("api_del_asistente_fallo", extra={"tenant": identity.business_slug, "error": type(exc).__name__})
        return _error(status.HTTP_503_SERVICE_UNAVAILABLE, "unavailable", "El asistente no pudo responder. Intenta de nuevo en un momento.")
    return reply_payload(result)
