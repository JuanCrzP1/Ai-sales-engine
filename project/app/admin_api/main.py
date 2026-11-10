"""Aplicación de la API del panel. Recibe los servicios ya construidos: no conoce la base de datos.

Dos modos, según reciba o no `verifier`:
- En la nube (`app/cloud_panel.py`): cada petición trae el token de la sesión de Neon Auth y cada usuario solo llega a sus
  negocios. Sin token válido, 401.
- En este equipo (`scripts/run_admin_api.py`, limitada a `127.0.0.1`), sin cuentas. Aunque alguien la sirviera en otra
  interfaz, solo atiende peticiones que vengan de este equipo. El `Host` y el `Origin` se comprueban porque un sitio web abierto en el navegador también
corre en este equipo: sin estas comprobaciones podría llamar a la API (falsificación de peticiones o `DNS rebinding`). No hay
CORS: el panel llega a través del proxy de Vite.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.admin_api.assistant_routes import router as assistant_router
from app.admin_api.errors import register_error_handlers
from app.admin_api.routes import router
from app.business_config_application.access import BusinessAccess
from app.business_config_application.assistant_lab import AssistantLabService
from app.business_config_application.ports import AccessTokenVerifier
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.contract import business_config_json_schema

logger = logging.getLogger("admin-api")

LOOPBACK_CLIENTS = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}
LOOPBACK_HOSTNAMES = {"127.0.0.1", "localhost", "[::1]"}
# El puerto de la interfaz del panel (`apps/admin-web/vite.config.ts`). El 4173 es el de su vista previa.
ADMIN_WEB_PORT = 5180
PANEL_ORIGINS = {
    f"http://127.0.0.1:{ADMIN_WEB_PORT}",
    f"http://localhost:{ADMIN_WEB_PORT}",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
}


def _hostname(host_header: str) -> str:
    """El nombre sin el puerto: `localhost:5180`, `127.0.0.1:8010` o `[::1]:8010`."""
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


def create_app(
    service: BusinessConfigService,
    assistant_lab: AssistantLabService | None = None,
    *,
    access: BusinessAccess | None = None,
    verifier: AccessTokenVerifier | None = None,
) -> FastAPI:
    """La API del panel. Sin `assistant_lab`, la inteligencia artificial y el área de pruebas responden que no están disponibles.

    Con `verifier` es la de la nube y necesita `access` con los miembros de cada negocio; sin él, la local."""
    cloud = verifier is not None
    if cloud and access is None:
        raise ValueError("la API de la nube necesita saber a qué negocios llega cada usuario")
    # Sin /docs ni /openapi.json: el único cliente es el panel y no hace falta anunciar las rutas.
    app = FastAPI(title="AI Sales Engine: API del panel", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.service = service
    app.state.assistant_lab = assistant_lab
    app.state.access = access or BusinessAccess(service)
    app.state.verifier = verifier
    app.state.contract_schema = business_config_json_schema()

    @app.middleware("http")
    async def guard(request: Request, call_next):
        refusal = None if cloud else _refusal(request)
        if refusal is not None:
            logger.warning("peticion_rechazada", extra={"reason": refusal})
            return JSONResponse({"code": "forbidden", "message": "Esta API solo atiende al panel en este equipo.", "issues": []}, status.HTTP_403_FORBIDDEN)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    register_error_handlers(app)
    app.include_router(router)
    app.include_router(assistant_router)
    return app
