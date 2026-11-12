"""Rutas de la atención humana (Configuración → Atención humana) y de las notificaciones de cada navegador.

Reciben la petición, llaman a `AttentionService` y `PushService` y serializan la respuesta. Los ajustes son de un negocio (solo de
quien pregunta); las notificaciones son de la persona: cada navegador o celular donde las activó.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Query, Request, Response, status

from app.admin_api.errors import ApiError
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.admin_api.schemas import attention_payload
from app.business_config_application.attention import AttentionService, PushService
from app.business_config_application.ports import EmailNotSent
from app.domain.business_config.errors import AssistantUnavailableError

router = APIRouter(prefix="/api")


def _attention(request: Request) -> AttentionService:
    service = getattr(request.app.state, "attention", None)
    if service is None:
        raise AssistantUnavailableError("la atención humana no está disponible en este servidor")
    return service


def _push(request: Request) -> PushService:
    service = getattr(request.app.state, "push", None)
    if service is None:
        raise ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, "Las notificaciones no están disponibles en este servidor.", code="push_unavailable")
    return service


Attention = Annotated[AttentionService, Depends(_attention)]
Push = Annotated[PushService, Depends(_push)]


@router.get("/businesses/{slug}/attention")
def get_attention(slug: BusinessSlug, user: CurrentUser, service: Attention) -> dict[str, Any]:
    return attention_payload(service.view(user, slug))


@router.put("/businesses/{slug}/attention")
def save_attention(slug: BusinessSlug, user: CurrentUser, service: Attention, body: Annotated[dict[str, Any], Body()]) -> dict[str, Any]:
    return attention_payload(service.save(user, slug, body))


@router.post("/businesses/{slug}/attention/test-email")
def send_test_email(slug: BusinessSlug, user: CurrentUser, service: Attention) -> dict[str, Any]:
    try:
        return {"sent_to": service.send_test_email(user, slug)}
    except EmailNotSent as exc:
        raise ApiError(status.HTTP_502_BAD_GATEWAY, str(exc), code="email_not_sent") from None


@router.get("/notifications/push")
def push_status(user: CurrentUser, service: Push, endpoint: Annotated[str | None, Query(max_length=1024)] = None) -> dict[str, Any]:
    """La clave pública de la plataforma (la pide el navegador para suscribirse) y si este navegador ya las tiene activadas."""
    return {"public_key": service.public_key(), "subscribed": service.status(user, endpoint)}


@router.post("/notifications/push", status_code=status.HTTP_204_NO_CONTENT)
def push_subscribe(user: CurrentUser, service: Push, body: Annotated[dict[str, Any], Body()]) -> Response:
    service.subscribe(user, body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/notifications/push/remove", status_code=status.HTTP_204_NO_CONTENT)
def push_unsubscribe(user: CurrentUser, service: Push, body: Annotated[dict[str, Any], Body()]) -> Response:
    service.unsubscribe(user, str(body.get("endpoint") or ""))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/notifications/push/test", status_code=status.HTTP_204_NO_CONTENT)
def push_test(user: CurrentUser, service: Push, body: Annotated[dict[str, Any], Body()]) -> Response:
    service.send_test(user, str(body.get("endpoint") or ""))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
