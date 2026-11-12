"""
Rutas de la API del motor.

Solo se publica lo que los canales necesitan: los webhooks de WhatsApp (Meta y el de código QR de cada negocio), la API del
asistente (`/assistant/messages`, con una clave de API del negocio), la revisión
periódica de la atención humana (protegida con `CRON_SECRET`) y, fuera de producción, la simulación (`/health` está en `app.main`).
La administración vive en la API del panel (`app.admin_api`).
"""
from fastapi import APIRouter

from app.api.controllers.assistant_api import router as assistant_api_router
from app.api.controllers.attention_tasks import router as attention_router
from app.api.controllers.simulation import router as simulation_router, simulation_enabled
from app.api.controllers.whatsapp_qr_webhook import router as whatsapp_qr_router
from app.api.controllers.whatsapp_webhook import router as whatsapp_webhook_router


def build_router() -> APIRouter:
    api = APIRouter()
    if simulation_enabled():
        api.include_router(simulation_router)
    api.include_router(whatsapp_webhook_router)
    api.include_router(whatsapp_qr_router)
    api.include_router(attention_router)
    api.include_router(assistant_api_router)
    return api


router = build_router()
