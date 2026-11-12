"""Notificaciones Web Push (RFC 8030), cifradas (RFC 8291, `aes128gcm`) y firmadas con VAPID (RFC 8292): implementa `PushSender`.

El cifrado lo hace `http_ece` y la firma `py_vapid` (las mismas piezas que usa `pywebpush`); el envío es una petición HTTP al
servicio de notificaciones del navegador. Solo se envía a direcciones de servicios conocidos (`domain/business_config/push.py`).
"""
from __future__ import annotations

import base64
import json
import os
import time
from collections.abc import Callable
from urllib.parse import urlsplit

import http_ece
import httpx
from cryptography.hazmat.primitives.asymmetric import ec
from py_vapid import Vapid02

from app.business_config_application.ports import PushOutcome
from app.domain.business_config.push import PUSH_TTL_SECONDS, PushMessage, PushSubscription, VapidKeys, allowed_endpoint

TIMEOUT = httpx.Timeout(10.0, connect=5.0)
DEFAULT_SUBJECT = "https://ai-sales-engine-panel.vercel.app"
# La firma vale 12 horas (los servicios aceptan hasta 24).
SIGNATURE_SECONDS = 12 * 60 * 60


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class WebPushSender:
    def __init__(
        self,
        keys: Callable[[], VapidKeys],
        *,
        subject: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._keys = keys
        self._subject = (subject or os.getenv("PANEL_URL") or DEFAULT_SUBJECT).strip()
        self._client = client

    def send(self, subscription: PushSubscription, message: PushMessage) -> PushOutcome:
        if not allowed_endpoint(subscription.endpoint):
            return PushOutcome("gone", "dirección de un servicio desconocido")
        payload = json.dumps({"title": message.title, "body": message.body, "url": message.url, "tag": message.tag}, ensure_ascii=False)
        body = http_ece.encrypt(
            payload.encode("utf-8"),
            salt=os.urandom(16),
            private_key=ec.generate_private_key(ec.SECP256R1()),
            dh=_decode(subscription.p256dh),
            auth_secret=_decode(subscription.auth),
            version="aes128gcm",
        )
        parts = urlsplit(subscription.endpoint)
        vapid = Vapid02.from_raw(self._keys().private_key.encode("ascii"))
        claims = {"sub": self._subject, "aud": f"{parts.scheme}://{parts.netloc}", "exp": int(time.time()) + SIGNATURE_SECONDS}
        headers = {
            **vapid.sign(claims),
            "Content-Encoding": "aes128gcm",
            "Content-Type": "application/octet-stream",
            "TTL": str(PUSH_TTL_SECONDS),
            "Urgency": "high",
        }
        try:
            if self._client is not None:
                response = self._client.post(subscription.endpoint, content=body, headers=headers, timeout=TIMEOUT)
            else:
                with httpx.Client(timeout=TIMEOUT) as client:
                    response = client.post(subscription.endpoint, content=body, headers=headers)
        except httpx.HTTPError as exc:
            return PushOutcome("failed", f"el servicio no respondió ({type(exc).__name__})")
        if response.status_code in (200, 201, 202):
            return PushOutcome("sent")
        if response.status_code in (404, 410):
            # El navegador quitó el permiso o la suscripción venció: hay que olvidarla.
            return PushOutcome("gone", f"el servicio dijo {response.status_code}")
        return PushOutcome("failed", f"el servicio respondió {response.status_code}")
