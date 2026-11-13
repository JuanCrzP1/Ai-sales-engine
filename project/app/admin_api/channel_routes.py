"""Rutas de los canales de cada negocio: WhatsApp por código QR (uazapi) y Telegram (el bot del negocio).

Reciben la petición, llaman al servicio del canal y serializan la respuesta. En WhatsApp el negocio no envía ni recibe servidores ni
tokens: son de la plataforma. En Telegram envía una sola vez el código de su bot, que nunca vuelve al panel. Si el canal no está
disponible, 503; si el bot ya está en otro negocio, 409; si el canal falla, 502. Siempre con un mensaje para el negocio, sin detalles
técnicos.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status

from app.admin_api.errors import ApiError
from app.admin_api.routes import BusinessSlug, ConfigurableSlug, CurrentUser
from app.admin_api.schemas import TelegramConnectRequest, telegram_payload, whatsapp_payload
from app.business_config_application.channels import TelegramChannelService, TelegramView, WhatsAppChannelService, WhatsAppView
from app.business_config_application.usage_limits import UsageGuard
from app.domain.business_config.channels import BotInUseError, ChannelError, ChannelUnavailableError

router = APIRouter(prefix="/api/businesses/{slug}/channels")


def _whatsapp(request: Request) -> WhatsAppChannelService:
    service = getattr(request.app.state, "whatsapp", None)
    if service is None:
        raise ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, "Los canales no están disponibles en este servidor.", code="unavailable")
    return service


def _telegram(request: Request) -> TelegramChannelService:
    service = getattr(request.app.state, "telegram", None)
    if service is None:
        raise ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, "Los canales no están disponibles en este servidor.", code="unavailable")
    return service


def _usage(request: Request) -> UsageGuard:
    return request.app.state.usage


WhatsApp = Annotated[WhatsAppChannelService, Depends(_whatsapp)]
Telegram = Annotated[TelegramChannelService, Depends(_telegram)]
Usage = Annotated[UsageGuard, Depends(_usage)]


def _run(action):
    try:
        return action()
    except ChannelUnavailableError as exc:
        raise ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc), code="channel_unavailable") from None
    except BotInUseError as exc:
        raise ApiError(status.HTTP_409_CONFLICT, str(exc), code="bot_in_use") from None
    except ChannelError as exc:
        raise ApiError(status.HTTP_502_BAD_GATEWAY, str(exc), code="channel_failed") from None


def _answer(action) -> dict[str, Any]:
    view: WhatsAppView = _run(action)
    return whatsapp_payload(view)


def _bot(action) -> dict[str, Any]:
    view: TelegramView = _run(action)
    return telegram_payload(view)


@router.get("/whatsapp")
def get_whatsapp(slug: BusinessSlug, whatsapp: WhatsApp) -> dict[str, Any]:
    return whatsapp_payload(whatsapp.get(slug))


@router.post("/whatsapp/connect")
def connect_whatsapp(slug: ConfigurableSlug, user: CurrentUser, whatsapp: WhatsApp, usage: Usage) -> dict[str, Any]:
    usage.channel_setup(user)
    return _answer(lambda: whatsapp.connect(slug))


@router.post("/whatsapp/new-code")
def new_whatsapp_code(slug: ConfigurableSlug, user: CurrentUser, whatsapp: WhatsApp, usage: Usage) -> dict[str, Any]:
    usage.channel_setup(user)
    return _answer(lambda: whatsapp.new_code(slug))


@router.get("/whatsapp/status")
def whatsapp_status(slug: ConfigurableSlug, whatsapp: WhatsApp, usage: Usage) -> dict[str, Any]:
    usage.channel_status(slug)
    return _answer(lambda: whatsapp.refresh(slug))


@router.post("/whatsapp/disconnect")
def disconnect_whatsapp(slug: ConfigurableSlug, whatsapp: WhatsApp) -> dict[str, Any]:
    return _answer(lambda: whatsapp.disconnect(slug))


# ---------------------------------------------------------------------------------------------------------- Telegram


@router.get("/telegram")
def get_telegram(slug: BusinessSlug, telegram: Telegram) -> dict[str, Any]:
    return telegram_payload(telegram.get(slug))


@router.post("/telegram/connect")
def connect_telegram(slug: ConfigurableSlug, user: CurrentUser, body: TelegramConnectRequest, telegram: Telegram, usage: Usage) -> dict[str, Any]:
    usage.channel_setup(user)
    return _bot(lambda: telegram.connect(slug, body.token))


@router.post("/telegram/reconnect")
def reconnect_telegram(slug: ConfigurableSlug, user: CurrentUser, telegram: Telegram, usage: Usage) -> dict[str, Any]:
    usage.channel_setup(user)
    return _bot(lambda: telegram.reconnect(slug))


@router.get("/telegram/status")
def telegram_status(slug: ConfigurableSlug, telegram: Telegram, usage: Usage) -> dict[str, Any]:
    usage.channel_status(slug)
    return _bot(lambda: telegram.refresh(slug))


@router.post("/telegram/disconnect")
def disconnect_telegram(slug: ConfigurableSlug, telegram: Telegram) -> dict[str, Any]:
    return _bot(lambda: telegram.disconnect(slug))
