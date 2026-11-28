"""`/internal/follow-up/run`: la revisión periódica del seguimiento (los mensajes a los clientes que dejaron de responder).

No es de usuarios: la llama Vercel cada 15 minutos (`project/vercel.json`, «schedules») con `Authorization: Bearer <CRON_SECRET>`,
como la de la atención humana. Sin `CRON_SECRET` configurado no atiende a nadie (503): la revisión sigue corriendo con el tráfico.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.controllers import whatsapp_qr_webhook
from app.api.controllers.attention_tasks import _authorized

router = APIRouter(prefix="/internal/follow-up", tags=["Seguimiento"])


@router.api_route("/run", methods=["GET", "POST"])
def run_follow_up(request: Request) -> dict[str, int | str]:
    _authorized(request)
    result = whatsapp_qr_webhook.run_follow_up_sweep()
    if result is None:
        return {"status": "busy"}
    return {"status": "ok", "checked": result.checked, "sent": result.sent, "skipped": result.skipped, "stopped": result.stopped}
