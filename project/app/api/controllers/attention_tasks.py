"""`/internal/attention/run`: la revisión periódica de la atención humana (la IA retoma los chats que nadie atendió a tiempo).

No es de usuarios: la llama Vercel cada 15 minutos (`project/vercel.json`, «schedules») con `Authorization: Bearer <CRON_SECRET>`.
Sin `CRON_SECRET` configurado no atiende a nadie (503): la revisión sigue corriendo con el tráfico del motor y del panel.
"""
from __future__ import annotations

import hmac
import os

from fastapi import APIRouter, HTTPException, Request, status

from app.api.controllers import whatsapp_qr_webhook

router = APIRouter(prefix="/internal/attention", tags=["Atención humana"])

MIN_SECRET_CHARS = 16


def _authorized(request: Request) -> None:
    secret = str(os.getenv("CRON_SECRET") or "").strip()
    if len(secret) < MIN_SECRET_CHARS:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No disponible")
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(token.strip().encode(), secret.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")


@router.api_route("/run", methods=["GET", "POST"])
def run_attention(request: Request) -> dict[str, int | str]:
    _authorized(request)
    result = whatsapp_qr_webhook.run_resume_sweep()
    if result is None:
        return {"status": "busy"}
    return {"status": "ok", "checked": result.checked, "resumed": result.resumed}
