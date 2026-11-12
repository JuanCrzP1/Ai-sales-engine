"""Correo con Resend (https://resend.com): implementa `EmailSender`.

La clave de Resend es de la plataforma (`RESEND_API_KEY`, en Vercel como *Sensitive*); el negocio nunca la ve. El remitente es
`EMAIL_FROM` (por ejemplo `AI Sales Engine <avisos@tudominio.com>`, con el dominio verificado en Resend). Sin dominio propio, Resend
solo permite su remitente de pruebas, `onboarding@resend.dev`, y solo entrega al correo de la cuenta de Resend.

Cada envío lleva una clave de idempotencia: si se reintenta el mismo aviso, Resend no manda el correo dos veces.
"""
from __future__ import annotations

import os

import httpx

from app.business_config_application.ports import EmailNotSent

RESEND_URL = "https://api.resend.com/emails"
DEFAULT_SENDER = "AI Sales Engine <onboarding@resend.dev>"
TIMEOUT = httpx.Timeout(15.0, connect=5.0)


class ResendEmailSender:
    def __init__(self, api_key: str | None = None, sender: str | None = None, *, client: httpx.Client | None = None) -> None:
        self._api_key = (api_key if api_key is not None else os.getenv("RESEND_API_KEY") or "").strip()
        self._sender = (sender if sender is not None else os.getenv("EMAIL_FROM") or "").strip() or DEFAULT_SENDER
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def send(self, *, to: list[str], subject: str, html: str, text: str, idempotency_key: str | None = None) -> str | None:
        if not self._api_key:
            raise EmailNotSent("El correo de avisos aún no está activado en la plataforma.")
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key[:256]
        payload = {"from": self._sender, "to": to[:10], "subject": subject[:200], "html": html, "text": text}
        try:
            if self._client is not None:
                response = self._client.post(RESEND_URL, json=payload, headers=headers, timeout=TIMEOUT)
            else:
                with httpx.Client(timeout=TIMEOUT) as client:
                    response = client.post(RESEND_URL, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise EmailNotSent(f"Resend no respondió ({type(exc).__name__}).") from exc
        if response.status_code >= 300:
            # El mensaje de Resend dice qué pasó (remitente sin verificar, clave inválida...); nunca trae la clave.
            try:
                reason = str(response.json().get("message") or "")[:200]
            except ValueError:
                reason = ""
            raise EmailNotSent(f"Resend rechazó el correo ({response.status_code}){f': {reason}' if reason else ''}.")
        try:
            return str(response.json().get("id") or "") or None
        except ValueError:
            return None
