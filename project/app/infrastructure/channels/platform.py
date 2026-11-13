"""El servidor de uazapi de la plataforma: `UAZAPI_BASE_URL` y `UAZAPI_ADMIN_TOKEN` (en Vercel, este último como *Sensitive*).

Son de quien opera la plataforma, no de cada negocio: con el token de administrador se crea una instancia por negocio. Sin ellas (o
con una dirección que no sirve), Canales dice que la conexión por código QR no está disponible y nada se rompe.

En este equipo, `WHATSAPP_SIMULATOR_URL` (y `WHATSAPP_SIMULATOR_TOKEN`, por defecto «simulador») cambia uazapi por el WhatsApp
simulado (`apps/wa-sim`): el panel y el motor le hablan con su código real, sin saber que es un simulador. Solo `http://localhost` o
`http://127.0.0.1`, y nunca en producción ni en Vercel: ahí se ignora y se registra.
"""
from __future__ import annotations

import os
import re

from app.domain.business_config.channels import UazapiPlatform, normalize_server_url
from app.utils.logger import logger

BASE_URL_ENV = "UAZAPI_BASE_URL"
ADMIN_TOKEN_ENV = "UAZAPI_ADMIN_TOKEN"
SIMULATOR_URL_ENV = "WHATSAPP_SIMULATOR_URL"
SIMULATOR_TOKEN_ENV = "WHATSAPP_SIMULATOR_TOKEN"
_LOCAL_SIMULATOR = re.compile(r"http://(localhost|127\.0\.0\.1):[0-9]{2,5}")


def _in_production() -> bool:
    return bool(os.getenv("VERCEL")) or any(str(os.getenv(name) or "").strip().lower() == "production" for name in ("ENV", "APP_ENV", "ENVIRONMENT"))


def simulator_url() -> str | None:
    """La dirección del WhatsApp simulado, o None si no se usa (o si se pidió donde no se puede: producción, o fuera de este equipo)."""
    raw = str(os.getenv(SIMULATOR_URL_ENV) or "").strip().rstrip("/")
    if not raw:
        return None
    if _in_production():
        logger.error("simulador_rechazado_en_produccion", extra={"variable": SIMULATOR_URL_ENV})
        return None
    if not _LOCAL_SIMULATOR.fullmatch(raw):
        logger.error("simulador_no_local", extra={"variable": SIMULATOR_URL_ENV})
        return None
    return raw


def is_simulator(server_url: str) -> bool:
    """Si esa dirección es la del WhatsApp simulado de este equipo (el único servidor local al que se le habla)."""
    local = simulator_url()
    return local is not None and str(server_url or "").rstrip("/") == local


def uazapi_platform() -> UazapiPlatform | None:
    """El servidor y el token de administrador de la plataforma, o None si faltan o la dirección no sirve. En este equipo, con el
    simulador configurado, el simulador."""
    local = simulator_url()
    if local is not None:
        return UazapiPlatform(local, str(os.getenv(SIMULATOR_TOKEN_ENV) or "simulador").strip())
    raw_url = str(os.getenv(BASE_URL_ENV) or "").strip()
    admin_token = str(os.getenv(ADMIN_TOKEN_ENV) or "").strip()
    if not raw_url or not admin_token:
        return None
    try:
        return UazapiPlatform(normalize_server_url(raw_url), admin_token)
    except ValueError as exc:
        logger.error("uazapi_direccion_invalida", extra={"variable": BASE_URL_ENV, "error": str(exc)})
        return None
