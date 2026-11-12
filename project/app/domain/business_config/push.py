"""Notificaciones en el navegador y en el celular (Web Push): qué suscripción se acepta y qué lleva cada notificación.

Cada persona activa las notificaciones en cada navegador o celular donde usa el panel; el navegador entrega una dirección de su
servicio de notificaciones (Google, Mozilla, Apple o Microsoft) y dos claves para cifrar lo que se le envía. Solo se aceptan
direcciones de esos servicios: el servidor nunca envía nada a una dirección cualquiera que llegue del navegador.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from urllib.parse import urlsplit

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError

# Los servicios de notificaciones de los navegadores.
PUSH_HOSTS = ("fcm.googleapis.com", "updates.push.services.mozilla.com", "push.services.mozilla.com", "web.push.apple.com")
PUSH_HOST_SUFFIXES = (".notify.windows.com", ".push.apple.com")
MAX_ENDPOINT_CHARS = 1024
MAX_DEVICE_CHARS = 120
# Cuánto guarda el servicio una notificación si el celular está apagado: un aviso de hace más de un día ya no sirve.
PUSH_TTL_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class PushSubscription:
    endpoint: str
    p256dh: str
    auth: str
    user_id: str = ""
    device: str | None = None


@dataclass(frozen=True)
class VapidKeys:
    """Las claves con las que la plataforma firma sus notificaciones. La pública, como la pide el navegador (`applicationServerKey`:
    el punto sin comprimir, en base64url); la privada, los 32 bytes del número en base64url (vacía si solo se pidió la pública)."""

    public_key: str
    private_key: str


@dataclass(frozen=True)
class PushMessage:
    """Lo que muestra la notificación y adónde lleva al tocarla (una ruta del panel)."""

    title: str
    body: str
    url: str
    tag: str


def _b64url(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def allowed_endpoint(endpoint: str) -> bool:
    parts = urlsplit(endpoint)
    host = (parts.hostname or "").lower()
    return parts.scheme == "https" and parts.port in (None, 443) and (host in PUSH_HOSTS or host.endswith(PUSH_HOST_SUFFIXES))


def validated_subscription(user_id: str, *, endpoint: object, p256dh: object, auth: object, device: object = None) -> PushSubscription:
    """La suscripción que manda el navegador, revisada: dirección de un servicio conocido y claves del tamaño correcto."""
    issues: list[FieldIssue] = []
    url = str(endpoint or "").strip()
    if not url or len(url) > MAX_ENDPOINT_CHARS or not allowed_endpoint(url):
        issues.append(FieldIssue("endpoint", "Este navegador no entregó una dirección de notificaciones conocida."))
    keys: dict[str, str] = {}
    for name, value, size in (("p256dh", p256dh, 65), ("auth", auth, 16)):
        text = str(value or "").strip()
        try:
            valid = len(text) < 200 and len(_b64url(text)) == size
        except (ValueError, binascii.Error, UnicodeEncodeError):
            valid = False
        if not valid:
            issues.append(FieldIssue(f"keys.{name}", "La clave de este navegador no es válida."))
        keys[name] = text
    if issues:
        raise InvalidFieldsError("No se pudieron activar las notificaciones en este navegador.", issues)
    label = " ".join(str(device or "").split())[:MAX_DEVICE_CHARS] or None
    return PushSubscription(endpoint=url, p256dh=keys["p256dh"], auth=keys["auth"], user_id=user_id, device=label)
