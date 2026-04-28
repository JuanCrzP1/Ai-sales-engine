"""
Definición de rutas principales de la API.
"""
from fastapi import APIRouter

from app.api.controllers.auth import router as auth_router
from app.api.controllers.bot_config import router as bot_config_router
from app.api.controllers.clientes import router as clientes_router
from app.api.controllers.conversaciones import router as conversaciones_router
from app.api.controllers.connector_config import router as connector_config_router
from app.api.controllers.dashboard import router as dashboard_router
from app.api.controllers.simulation import router as simulation_router
from app.api.controllers.whatsapp_webhook import router as whatsapp_webhook_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(clientes_router)
router.include_router(conversaciones_router)
router.include_router(bot_config_router)
router.include_router(connector_config_router)
router.include_router(dashboard_router)
router.include_router(simulation_router)
router.include_router(whatsapp_webhook_router)
