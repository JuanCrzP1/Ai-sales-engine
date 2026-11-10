"""Rutas de los canales de cada negocio: por ahora WhatsApp por código QR (uazapi).

Reciben la petición, llaman a `WhatsAppChannelService` y serializan la respuesta. El token entra por aquí y nunca sale: las respuestas
solo dicen sus últimos caracteres. Un dato que el servidor de uazapi rechaza vuelve como 422 con su campo; si el servidor no
responde, 502.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status

from app.admin_api.errors import UNPROCESSABLE, ApiError
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.admin_api.schemas import SaveWhatsAppChannel, whatsapp_payload
from app.business_config_application.channels import WhatsAppChannelService, WhatsAppView
from app.business_config_application.usage_limits import UsageGuard
from app.domain.business_config.channels import ChannelError

router = APIRouter(prefix="/api/businesses/{slug}/channels")


def _whatsapp(request: Request) -> WhatsAppChannelService:
    service = getattr(request.app.state, "whatsapp", None)
    if service is None:
        raise ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, "Los canales no están disponibles en este servidor.", code="unavailable")
    return service


def _usage(request: Request) -> UsageGuard:
    return request.app.state.usage


WhatsApp = Annotated[WhatsAppChannelService, Depends(_whatsapp)]
Usage = Annotated[UsageGuard, Depends(_usage)]


def _answer(action) -> dict[str, Any]:
    try:
        view: WhatsAppView = action()
    except ChannelError as exc:
        if exc.field:
            raise ApiError(UNPROCESSABLE, str(exc), code="invalid", issues=[{"path": exc.field, "message": str(exc)}]) from None
        raise ApiError(status.HTTP_502_BAD_GATEWAY, str(exc), code="channel_unavailable") from None
    return whatsapp_payload(view)


@router.get("/whatsapp")
def get_whatsapp(slug: BusinessSlug, whatsapp: WhatsApp) -> dict[str, Any]:
    return whatsapp_payload(whatsapp.get(slug))


@router.put("/whatsapp")
def save_whatsapp(slug: BusinessSlug, body: SaveWhatsAppChannel, user: CurrentUser, whatsapp: WhatsApp, usage: Usage) -> dict[str, Any]:
    usage.channel_setup(user)
    return _answer(lambda: whatsapp.configure(slug, server_url=body.server_url, token=body.token))


@router.post("/whatsapp/connect")
def connect_whatsapp(slug: BusinessSlug, user: CurrentUser, whatsapp: WhatsApp, usage: Usage) -> dict[str, Any]:
    usage.channel_setup(user)
    return _answer(lambda: whatsapp.connect(slug))


@router.get("/whatsapp/status")
def whatsapp_status(slug: BusinessSlug, whatsapp: WhatsApp, usage: Usage) -> dict[str, Any]:
    usage.channel_status(slug)
    return _answer(lambda: whatsapp.refresh(slug))


@router.post("/whatsapp/disconnect")
def disconnect_whatsapp(slug: BusinessSlug, whatsapp: WhatsApp) -> dict[str, Any]:
    return _answer(lambda: whatsapp.disconnect(slug))


@router.delete("/whatsapp", status_code=status.HTTP_204_NO_CONTENT)
def remove_whatsapp(slug: BusinessSlug, whatsapp: WhatsApp) -> None:
    whatsapp.remove(slug)
