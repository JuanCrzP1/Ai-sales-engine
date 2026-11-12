"""La dirección a la que uazapi envía los mensajes de cada negocio: la dirección pública del motor más la ruta de los canales.

Es `ENGINE_PUBLIC_URL` (en este equipo, la de ngrok, que `run_local.sh` toma sola) o, en Vercel, el dominio de producción del
proyecto. Sin ella la conexión funciona, pero los mensajes no llegan al motor, y el panel lo avisa.
"""
from __future__ import annotations

import os

# La ruta del webhook en el motor (`app/api/controllers/whatsapp_qr_webhook.py`), sin el prefijo de la API.
WEBHOOK_PATH = "/channels/whatsapp"
# El panel publicado. `PANEL_URL` lo cambia (en este equipo, los lanzadores ponen el panel local).
PUBLIC_PANEL_URL = "https://ai-sales-engine-panel.vercel.app"


def panel_url() -> str:
    """La dirección del panel: adonde lleva la raíz del motor y los enlaces de los correos de aviso."""
    return (str(os.getenv("PANEL_URL") or "").strip() or PUBLIC_PANEL_URL).rstrip("/")


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


# La API del asistente (`app/api/controllers/assistant_api.py`), sin el prefijo de la API.
ASSISTANT_API_PATH = "/assistant/messages"


def assistant_api_url(api_prefix: str) -> str | None:
    """La dirección pública de la API del asistente, o None si el motor no tiene una."""
    public = engine_public_url()
    return f"{public}{api_prefix}{ASSISTANT_API_PATH}" if public else None


# El servidor MCP vive en la API del panel: en la nube, el panel reenvía `/api/*` al motor (`apps/admin-web/vercel.json`).
MCP_PATH = "/api/mcp"


def mcp_url() -> str:
    """La dirección del servidor MCP para pegar en un agente: la del panel publicado más `/api/mcp`."""
    return f"{panel_url()}{MCP_PATH}"


def local_mcp_url(port: int) -> str:
    """En este equipo, la API del panel directamente (solo atiende a este equipo)."""
    return f"http://127.0.0.1:{port}{MCP_PATH}"
