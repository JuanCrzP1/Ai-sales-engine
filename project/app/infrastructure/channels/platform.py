"""El servidor de uazapi de la plataforma: `UAZAPI_BASE_URL` y `UAZAPI_ADMIN_TOKEN` (en Vercel, este último como *Sensitive*).

Son de quien opera la plataforma, no de cada negocio: con el token de administrador se crea una instancia por negocio. Sin ellas (o
con una dirección que no sirve), Canales dice que la conexión por código QR no está disponible y nada se rompe.
"""
from __future__ import annotations

import os

from app.domain.business_config.channels import UazapiPlatform, normalize_server_url
from app.utils.logger import logger

BASE_URL_ENV = "UAZAPI_BASE_URL"
ADMIN_TOKEN_ENV = "UAZAPI_ADMIN_TOKEN"


def uazapi_platform() -> UazapiPlatform | None:
    """El servidor y el token de administrador de la plataforma, o None si faltan o la dirección no sirve."""
    raw_url = str(os.getenv(BASE_URL_ENV) or "").strip()
    admin_token = str(os.getenv(ADMIN_TOKEN_ENV) or "").strip()
    if not raw_url or not admin_token:
        return None
    try:
        return UazapiPlatform(normalize_server_url(raw_url), admin_token)
    except ValueError as exc:
        logger.error("uazapi_direccion_invalida", extra={"variable": BASE_URL_ENV, "error": str(exc)})
        return None
