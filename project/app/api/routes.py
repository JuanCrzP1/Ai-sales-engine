"""
Definición de rutas principales de la API.

En producción solo se publica lo que los canales necesitan: el webhook de WhatsApp (y `/health`, en `app.main`). Las rutas de
administración del sistema de cuentas anterior no se publican allí: `/auth/register` guardaría negocios y usuarios sin
autenticación, y el panel no las usa. `ENABLE_LEGACY_ADMIN_API=1` las publica igual.
"""
import os

from fastapi import APIRouter

from app.api.controllers.auth import router as auth_router
from app.api.controllers.bot_config import router as bot_config_router
from app.api.controllers.clientes import router as clientes_router
from app.api.controllers.conversaciones import router as conversaciones_router
from app.api.controllers.connector_config import router as connector_config_router
from app.api.controllers.dashboard import router as dashboard_router
from app.api.controllers.simulation import router as simulation_router, simulation_enabled
from app.api.controllers.whatsapp_webhook import router as whatsapp_webhook_router
from app.config import settings

LEGACY_ADMIN_ROUTERS = (auth_router, clientes_router, conversaciones_router, bot_config_router, connector_config_router, dashboard_router)


def legacy_admin_api_enabled() -> bool:
    explicit = str(os.getenv("ENABLE_LEGACY_ADMIN_API") or "").strip().lower()
    if explicit:
        return explicit in {"1", "true", "yes"}
    # Vercel define `VERCEL` en sus despliegues: allí es producción aunque falte `MODE`.
    in_production = str(settings.mode or "").strip().lower() == "production" or bool(os.getenv("VERCEL"))
    return not in_production


def build_router() -> APIRouter:
    api = APIRouter()
    if legacy_admin_api_enabled():
        for legacy_router in LEGACY_ADMIN_ROUTERS:
            api.include_router(legacy_router)
    if simulation_enabled():
        api.include_router(simulation_router)
    api.include_router(whatsapp_webhook_router)
    return api


router = build_router()
