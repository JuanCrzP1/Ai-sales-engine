"""Canales del negocio: WhatsApp conectado por código QR con uazapi y Telegram con el bot del propio negocio.

Hay dos formas de conectar WhatsApp: por código QR (uazapi, no oficial: WhatsApp puede bloquear números que envían mensajes masivos)
y por la API oficial de Meta (próximamente). El servidor de uazapi y su token de administrador son de la plataforma, no del negocio:
el negocio solo toca «Conectar» y escanea el QR. Con el token de administrador se crea una instancia para cada negocio, y el token
de esa instancia se guarda cifrado. El negocio nunca ve ni el servidor ni los tokens.

El webhook de cada negocio tiene un identificador secreto en su ruta: así el motor sabe de qué negocio es cada mensaje sin buscarlo
por número.

Telegram es oficial y gratis: el negocio crea su bot con @BotFather y pega el código (token) que le da. Se guarda cifrado, el webhook
se registra solo y cada aviso de Telegram trae una firma secreta (`telegram_webhook_secret`) que solo conoce quien tiene el token.
Cada cliente de Telegram se identifica como `tg-<id del chat>`: así nunca se cruza con un número de WhatsApp en la memoria del
asistente. Un bot solo atiende chats privados y nunca puede escribirle primero a nadie.
"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError

WHATSAPP = "whatsapp"
UAZAPI = "uazapi"
TELEGRAM = "telegram"
TELEGRAM_API = "https://api.telegram.org"
TELEGRAM_CONTACT_PREFIX = "tg-"
# El código que da @BotFather: el id del bot, dos puntos y el secreto (`7123456789:AAH...`).
BOT_IN_USE = "Ese bot ya está conectado en otro negocio. Crea otro bot en @BotFather para este negocio o desconéctalo del otro."
_BOT_TOKEN = re.compile(r"^(\d{5,16}):[A-Za-z0-9_-]{30,60}$")

ConnectionStatus = Literal["disconnected", "connecting", "connected"]
CONNECTION_STATUSES: tuple[ConnectionStatus, ...] = ("disconnected", "connecting", "connected")

# Nombres de máquina que nunca son un servidor público.
_LOCAL_HOSTS = {"localhost", "localhost.localdomain", "ip6-localhost", "ip6-loopback"}
_LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home.arpa")


class ChannelError(RuntimeError):
    """El servidor de WhatsApp no pudo hacer algo. El mensaje es para el negocio, sin detalles técnicos.

    `gone`: la instancia del negocio ya no existe en el servidor (la borró, venció o su token dejó de valer); conectar crea otra."""

    def __init__(self, message: str, *, gone: bool = False) -> None:
        super().__init__(message)
        self.gone = gone


class BotInUseError(ChannelError):
    """El bot de Telegram ya está conectado en otro negocio."""


class ChannelUnavailableError(ChannelError):
    """La plataforma no tiene listo ese canal (le falta su servidor o la dirección pública del motor). Lo arregla quien la opera."""


class WhatsAppUnavailableError(ChannelUnavailableError):
    """La plataforma no tiene configurado el servidor de WhatsApp por código QR, o le falta su dirección pública."""


def is_public_address(address: str) -> bool:
    """Si una IP es pública: ni privada, ni local, ni reservada (el servidor nunca llama a la red interna)."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_global and not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved)


def normalize_server_url(raw: str) -> str:
    """La dirección del servidor, normalizada a `https://servidor[:puerto]`. Solo https, sin usuario, ruta ni consulta, y nunca una
    máquina local o una IP privada. Lanza `ValueError` si no sirve."""
    text = str(raw or "").strip().rstrip("/")
    if not text:
        raise ValueError("falta la dirección del servidor de uazapi")
    parts = urlsplit(text if "://" in text else f"https://{text}")
    host = (parts.hostname or "").lower()
    if parts.scheme != "https":
        raise ValueError("la dirección del servidor de uazapi debe empezar por https://")
    if not host or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ("", "/"):
        raise ValueError("la dirección del servidor de uazapi debe ser solo https://servidor")
    if host in _LOCAL_HOSTS or host.endswith(_LOCAL_SUFFIXES) or "." not in host:
        raise ValueError("el servidor de uazapi debe ser público")
    try:
        ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        pass
    else:
        if not is_public_address(host.strip("[]")):
            raise ValueError("el servidor de uazapi debe ser público")
    port = f":{parts.port}" if parts.port and parts.port != 443 else ""
    return f"https://{host}{port}"


def phone_digits(value: str | None) -> str:
    """El número sin `+`, espacios ni el dominio de WhatsApp (`573001234567@s.whatsapp.net` → `573001234567`)."""
    return "".join(char for char in str(value or "").split("@")[0].split(":")[0] if char.isdigit())


@dataclass(frozen=True)
class UazapiPlatform:
    """El servidor de uazapi de la plataforma y su token de administrador (variables `UAZAPI_BASE_URL` y `UAZAPI_ADMIN_TOKEN`)."""

    server_url: str
    admin_token: str

    def __repr__(self) -> str:  # el token nunca llega a un registro
        return f"UazapiPlatform(server_url={self.server_url!r})"


@dataclass(frozen=True)
class WhatsAppConnection:
    """Lo que el panel muestra de la conexión: nunca el servidor ni los tokens."""

    status: ConnectionStatus
    phone: str | None = None
    profile_name: str | None = None


@dataclass(frozen=True)
class ChannelSecrets:
    """Lo necesario para hablar con el canal de este negocio: en WhatsApp, su instancia de uazapi; en Telegram, su bot (el servidor
    es la API de Telegram y el token, el del bot). Solo lo usan el servicio del canal y el motor."""

    tenant_slug: str
    server_url: str
    instance_token: str
    webhook_id: str
    channel: str = WHATSAPP

    def __repr__(self) -> str:  # el token nunca llega a un registro
        return f"ChannelSecrets(tenant_slug={self.tenant_slug!r}, channel={self.channel!r})"


@dataclass(frozen=True)
class ProviderStatus:
    """El estado que informa el servidor de uazapi."""

    status: ConnectionStatus
    qrcode: str | None = None
    paircode: str | None = None
    phone: str | None = None
    profile_name: str | None = None


@dataclass(frozen=True)
class IncomingMessage:
    """Un mensaje de un cliente, ya filtrado: no es del propio negocio, ni de un grupo, ni lo envió la API (ni otro bot).

    `kind` es el tipo (`conversations.KINDS`); `text` es el texto o la leyenda de un archivo (puede venir vacía)."""

    message_id: str
    # El contacto en el canal: el número en WhatsApp, `tg-<id del chat>` en Telegram.
    phone: str
    contact_name: str | None
    text: str
    kind: str = "text"
    mime_type: str | None = None
    file_name: str | None = None
    # Con qué se descarga el archivo, si no es el id del mensaje (en Telegram, el `file_id`).
    media_ref: str | None = None


@dataclass(frozen=True)
class DeliveryReceipt:
    """El aviso del canal de que lo que salió fue entregado o leído."""

    message_ids: tuple[str, ...]
    status: str


# ---------------------------------------------------------------------------------------------------------- Telegram


@dataclass(frozen=True)
class TelegramBot:
    """El bot que respondió Telegram al revisar el código: su id, su usuario (sin @) y su nombre."""

    id: str
    username: str
    name: str


@dataclass(frozen=True)
class TelegramConnection:
    """Lo que el panel muestra del bot del negocio: nunca el token. `disconnected` con bot guardado: Telegram rechazó el código."""

    status: ConnectionStatus
    bot_username: str | None = None
    bot_name: str | None = None


def validated_bot_token(raw: object) -> str:
    """El código del bot sin espacios, o `InvalidFieldsError` (campo `token`) si no tiene la forma del que da @BotFather."""
    token = "".join(str(raw or "").split())
    if not _BOT_TOKEN.match(token):
        message = (
            "Pega el código que te dio @BotFather" if not token
            else "Ese no parece el código de un bot. Cópialo completo desde @BotFather: se ve así, 7123456789:AAH…"
        )
        raise InvalidFieldsError(message, [FieldIssue("token", message)])
    return token


def bot_id_of(token: str) -> str:
    """El id del bot, que va antes de los dos puntos del código (no es secreto)."""
    return token.split(":", 1)[0]


def telegram_contact_ref(chat_id: object) -> str:
    return f"{TELEGRAM_CONTACT_PREFIX}{chat_id}"


def telegram_chat_id(contact_ref: str) -> str:
    """El id del chat de un contacto de Telegram (`tg-123` → `123`). Lanza `ChannelError` si no es de Telegram."""
    raw = str(contact_ref or "")
    chat = raw[len(TELEGRAM_CONTACT_PREFIX):] if raw.startswith(TELEGRAM_CONTACT_PREFIX) else ""
    if not chat.lstrip("-").isdigit():
        raise ChannelError("Este chat no es de Telegram.")
    return chat


def telegram_webhook_secret(token: str, webhook_id: str) -> str:
    """La firma que Telegram envía en cada aviso (`X-Telegram-Bot-Api-Secret-Token`): sale del token del bot y del webhook del negocio,
    así que nadie sin el token puede hacerse pasar por Telegram, y cambia si el negocio cambia de bot."""
    return hmac.new(token.encode("utf-8"), webhook_id.encode("utf-8"), hashlib.sha256).hexdigest()
