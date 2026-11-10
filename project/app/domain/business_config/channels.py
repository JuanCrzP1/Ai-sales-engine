"""Canales del negocio: por ahora, WhatsApp conectado por código QR con un servidor de uazapi.

Hay dos formas de conectar WhatsApp: por código QR (uazapi, no oficial: WhatsApp puede bloquear números que envían mensajes masivos)
y por la API oficial de Meta (próximamente). Cada negocio usa su propio servidor y su propio token, que se guarda cifrado. Si pega el
token de administrador del servidor, se crea una instancia solo para él y se guarda su token; el de administrador también queda
cifrado, para volver a crearla si el servidor la borra (los servidores de prueba la borran a la hora).

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


class ChannelError(ValueError):
    """Un dato del canal no es válido o el proveedor lo rechazó. El mensaje es para el negocio."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


def is_public_address(address: str) -> bool:
    """Si una IP es pública: ni privada, ni local, ni reservada (el panel nunca llama a la red interna)."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_global and not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved)


def normalize_server_url(raw: str) -> str:
    """La dirección del servidor, normalizada a `https://servidor[:puerto]`. Solo https, sin usuario, ruta ni consulta, y nunca una
    máquina local o una IP privada: el servidor del panel la llama y no puede servir para entrar a la red interna."""
    text = str(raw or "").strip().rstrip("/")
    if not text:
        raise ChannelError("Escribe la dirección de tu servidor de uazapi.", field="server_url")
    parts = urlsplit(text if "://" in text else f"https://{text}")
    host = (parts.hostname or "").lower()
    if parts.scheme != "https":
        raise ChannelError("La dirección del servidor debe empezar por https://.", field="server_url")
    if not host or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ("", "/"):
        raise ChannelError("Escribe solo la dirección del servidor, por ejemplo https://free.uazapi.com.", field="server_url")
    if host in _LOCAL_HOSTS or host.endswith(_LOCAL_SUFFIXES) or "." not in host:
        raise ChannelError("La dirección debe ser la de un servidor público.", field="server_url")
    try:
        ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        pass
    else:
        if not is_public_address(host.strip("[]")):
            raise ChannelError("La dirección debe ser la de un servidor público.", field="server_url")
    port = f":{parts.port}" if parts.port and parts.port != 443 else ""
    return f"https://{host}{port}"


def token_hint(token: str) -> str:
    """Los últimos caracteres del token, para reconocerlo sin mostrarlo."""
    return f"…{token.strip()[-4:]}" if len(token.strip()) >= 8 else "…"


def phone_digits(value: str | None) -> str:
    """El número sin `+`, espacios ni el dominio de WhatsApp (`573001234567@s.whatsapp.net` → `573001234567`)."""
    return "".join(char for char in str(value or "").split("@")[0].split(":")[0] if char.isdigit())


@dataclass(frozen=True)
class WhatsAppConnection:
    """Lo que el panel muestra de la conexión: nunca los tokens."""

    provider: str
    server_url: str
    status: ConnectionStatus
    token_hint: str
    has_admin_token: bool
    phone: str | None = None
    profile_name: str | None = None


@dataclass(frozen=True)
class WhatsAppSecrets:
    """Lo necesario para hablar con el servidor de este negocio. Solo lo usan el servicio del canal y el motor."""

    tenant_slug: str
    server_url: str
    instance_token: str
    admin_token: str | None
    webhook_id: str


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
    """Un mensaje de texto de un cliente, ya filtrado: no es del propio negocio, ni de un grupo, ni lo envió la API."""

    message_id: str
    phone: str
    contact_name: str | None
    text: str
