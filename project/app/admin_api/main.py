"""Aplicación de la API local del panel. Se arranca con `scripts/run_admin_api.py`, que la limita a `127.0.0.1`.

Recibe el servicio ya construido: no conoce la base de datos. Aunque alguien la sirviera en otra interfaz, solo atiende
peticiones que vengan de este equipo. El `Host` y el `Origin` se comprueban porque un sitio web abierto en el navegador también
corre en este equipo: sin estas comprobaciones podría llamar a la API (falsificación de peticiones o `DNS rebinding`). No hay
CORS: el panel llega a través del proxy de Vite.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.admin_api.errors import register_error_handlers
from app.admin_api.routes import router
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.contract import business_config_json_schema

logger = logging.getLogger("admin-api")

LOOPBACK_CLIENTS = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}
LOOPBACK_HOSTNAMES = {"127.0.0.1", "localhost", "[::1]"}
PANEL_ORIGINS = {
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
}


def _hostname(host_header: str) -> str:
    """El nombre sin el puerto: `localhost:5173`, `127.0.0.1:8010` o `[::1]:8010`."""
    if host_header.startswith("["):
        return host_header.split("]", 1)[0] + "]"
    return host_header.split(":", 1)[0]


def _refusal(request: Request) -> str | None:
    if request.client is None or request.client.host not in LOOPBACK_CLIENTS:
        return "client"
    if _hostname(request.headers.get("host", "")) not in LOOPBACK_HOSTNAMES:
        return "host"
    origin = request.headers.get("origin")
    if origin is not None and origin not in PANEL_ORIGINS:
        return "origin"
    return None


def create_app(service: BusinessConfigService) -> FastAPI:
    # Sin /docs ni /openapi.json: el único cliente es el panel y no hace falta anunciar las rutas.
    app = FastAPI(title="AI Sales Engine: API local del panel", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.service = service
    app.state.contract_schema = business_config_json_schema()

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        refusal = _refusal(request)
        if refusal is not None:
            logger.warning("peticion_rechazada", extra={"reason": refusal})
            return JSONResponse({"code": "forbidden", "message": "Esta API solo atiende al panel en este equipo.", "issues": []}, status.HTTP_403_FORBIDDEN)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    register_error_handlers(app)
    app.include_router(router)
    return app
