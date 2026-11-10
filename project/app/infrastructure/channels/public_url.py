"""La dirección a la que uazapi envía los mensajes de cada negocio: la dirección pública del motor más la ruta de los canales.

Es `ENGINE_PUBLIC_URL` (en este equipo, la de ngrok, que `run_local.sh` toma sola) o, en Vercel, el dominio de producción del
proyecto. Sin ella la conexión funciona, pero los mensajes no llegan al motor, y el panel lo avisa.
"""
from __future__ import annotations

import os

# La ruta del webhook en el motor (`app/api/controllers/whatsapp_qr_webhook.py`), sin el prefijo de la API.
WEBHOOK_PATH = "/channels/whatsapp"


def engine_public_url() -> str | None:
    """La dirección pública del motor, o None si no se conoce (por ejemplo, en este equipo sin ngrok)."""
    explicit = str(os.getenv("ENGINE_PUBLIC_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    vercel = str(os.getenv("VERCEL_PROJECT_PRODUCTION_URL") or "").strip().rstrip("/")
    return f"https://{vercel}" if vercel else None


def webhook_base(api_prefix: str) -> str | None:
    public = engine_public_url()
    return f"{public}{api_prefix}{WEBHOOK_PATH}" if public else None
