"""Rutas de los canales de cada negocio: por ahora WhatsApp por código QR (uazapi).

Reciben la petición, llaman a `WhatsAppChannelService` y serializan la respuesta. El negocio no envía ni recibe servidores ni
tokens: son de la plataforma. Si la conexión no está disponible, 503; si el servidor de WhatsApp falla, 502. Los dos con un mensaje
para el negocio, sin detalles técnicos.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status

from app.admin_api.errors import ApiError
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.admin_api.schemas import whatsapp_payload
from app.business_config_application.channels import WhatsAppChannelService, WhatsAppView
from app.business_config_application.usage_limits import UsageGuard
from app.domain.business_config.channels import ChannelError, WhatsAppUnavailableError

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
    except WhatsAppUnavailableError as exc:
        raise ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc), code="channel_unavailable") from None
    except ChannelError as exc:
        raise ApiError(status.HTTP_502_BAD_GATEWAY, str(exc), code="channel_failed") from None
    return whatsapp_payload(view)


@router.get("/whatsapp")
def get_whatsapp(slug: BusinessSlug, whatsapp: WhatsApp) -> dict[str, Any]:
    return whatsapp_payload(whatsapp.get(slug))


@router.post("/whatsapp/connect")
def connect_whatsapp(slug: BusinessSlug, user: CurrentUser, whatsapp: WhatsApp, usage: Usage) -> dict[str, Any]:
    usage.channel_setup(user)
    return _answer(lambda: whatsapp.connect(slug))


@router.post("/whatsapp/new-code")
def new_whatsapp_code(slug: BusinessSlug, user: CurrentUser, whatsapp: WhatsApp, usage: Usage) -> dict[str, Any]:
    usage.channel_setup(user)
    return _answer(lambda: whatsapp.new_code(slug))


@router.get("/whatsapp/status")
def whatsapp_status(slug: BusinessSlug, whatsapp: WhatsApp, usage: Usage) -> dict[str, Any]:
    usage.channel_status(slug)
    return _answer(lambda: whatsapp.refresh(slug))


@router.post("/whatsapp/disconnect")
def disconnect_whatsapp(slug: BusinessSlug, whatsapp: WhatsApp) -> dict[str, Any]:
    return _answer(lambda: whatsapp.disconnect(slug))
