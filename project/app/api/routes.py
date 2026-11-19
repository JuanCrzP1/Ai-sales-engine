"""
Rutas de la API del motor.

Solo se publica lo que los canales necesitan: el webhook de WhatsApp por código QR de cada negocio y el de Telegram, la API del
asistente (`/assistant/messages`, con una clave de API del negocio) y la revisión periódica de la atención humana (protegida con
`CRON_SECRET`); `/health` está en `app.main`. La administración vive en la API del panel (`app.admin_api`) y «Probar asistente»
del panel es donde se prueba el asistente.
"""
from fastapi import APIRouter

from app.api.controllers.assistant_api import router as assistant_api_router
from app.api.controllers.attention_tasks import router as attention_router
from app.api.controllers.telegram_webhook import router as telegram_router
from app.api.controllers.whatsapp_qr_webhook import router as whatsapp_qr_router


def build_router() -> APIRouter:
    api = APIRouter()
    api.include_router(whatsapp_qr_router)
    api.include_router(telegram_router)
    api.include_router(attention_router)
    api.include_router(assistant_api_router)
    return api


router = build_router()
