"""Canales del negocio: por ahora, WhatsApp conectado por código QR con uazapi.

Hay dos formas de conectar WhatsApp: por código QR (uazapi, no oficial: WhatsApp puede bloquear números que envían mensajes masivos)
y por la API oficial de Meta (próximamente). El servidor de uazapi y su token de administrador son de la plataforma, no del negocio:
el negocio solo toca «Conectar» y escanea el QR. Con el token de administrador se crea una instancia para cada negocio, y el token
de esa instancia se guarda cifrado. El negocio nunca ve ni el servidor ni los tokens.

El webhook de cada negocio tiene un identificador secreto en su ruta: así el motor sabe de qué negocio es cada mensaje sin buscarlo
por número.
"""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

WHATSAPP = "whatsapp"
UAZAPI = "uazapi"

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


class WhatsAppUnavailableError(ChannelError):
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
class WhatsAppSecrets:
    """Lo necesario para hablar con la instancia de este negocio. Solo lo usan el servicio del canal y el motor."""

    tenant_slug: str
    server_url: str
    instance_token: str
    webhook_id: str

    def __repr__(self) -> str:  # el token nunca llega a un registro
        return f"WhatsAppSecrets(tenant_slug={self.tenant_slug!r})"


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
    """Un mensaje de un cliente, ya filtrado: no es del propio negocio, ni de un grupo, ni lo envió la API.

    `kind` es el tipo (`conversations.KINDS`); `text` es el texto o la leyenda de un archivo (puede venir vacía)."""

    message_id: str
    phone: str
    contact_name: str | None
    text: str
    kind: str = "text"
    mime_type: str | None = None
    file_name: str | None = None


@dataclass(frozen=True)
class DeliveryReceipt:
    """El aviso del canal de que lo que salió fue entregado o leído."""

    message_ids: tuple[str, ...]
    status: str
