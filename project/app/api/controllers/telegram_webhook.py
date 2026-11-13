"""Webhook de Telegram: recibe los mensajes que los clientes le escriben al bot de cada negocio.

Cada negocio tiene su propia ruta, `/channels/telegram/{webhook_id}`, con un identificador secreto que registra el panel al conectar
el bot. Además, solo cuenta un aviso que trae la firma del negocio en `X-Telegram-Bot-Api-Secret-Token` (sale del token del bot: nadie
sin él puede hacerse pasar por Telegram).

La ruta solo recibe y contesta enseguida; el mensaje sigue el mismo camino que uno de WhatsApp (`app/application/channels/inbound.py`,
armado en `whatsapp_qr_webhook.build_inbound`): se guarda en la bandeja sin duplicados y, después de contestarle a Telegram, el
asistente lo entiende y responde, o lo pasa a una persona.
"""
from __future__ import annotations

import hmac
from types import SimpleNamespace

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.api.controllers import whatsapp_qr_webhook
from app.domain.business_config.channels import TELEGRAM, ChannelSecrets, telegram_webhook_secret
from app.domain.business_config.errors import BusinessConfigError
from app.infrastructure.business_config import runtime_access
from app.infrastructure.channels import telegram
from app.utils.logger import logger

router = APIRouter(prefix="/channels", tags=["Telegram"])

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"

# Telegram no avisa cambios de conexión ni recibos, y lo que el bot envía no vuelve como aviso: solo hay mensajes de clientes.
_TELEGRAM = SimpleNamespace(
    connection_event=lambda _payload: None,
    parse_receipt=lambda _payload: None,
    parse_own_message=lambda _payload: None,
    parse_incoming=telegram.parse_update,
)


def _connection(webhook_id: str) -> ChannelSecrets:
    if len(webhook_id) < whatsapp_qr_webhook.MIN_WEBHOOK_ID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    try:
        secrets = runtime_access.channel_for_webhook(webhook_id, TELEGRAM)
    except BusinessConfigError as exc:
        logger.error("telegram_almacen_no_disponible", extra={"error": type(exc).__name__})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No disponible") from exc
    if secrets is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    return secrets


@router.post("/telegram/{webhook_id}")
async def receive_telegram(webhook_id: str, request: Request, background: BackgroundTasks) -> dict[str, str]:
    secrets = _connection(webhook_id)
    signature = request.headers.get(SECRET_HEADER) or ""
    if not hmac.compare_digest(signature, telegram_webhook_secret(secrets.instance_token, secrets.webhook_id)):
        logger.warning("telegram_rechazado", extra={"tenant": secrets.tenant_slug, "reason": "firma_distinta"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuerpo no válido") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuerpo no válido")

    inbound = whatsapp_qr_webhook.build_inbound()
    received = inbound.receive(secrets, payload, parse=_TELEGRAM)
    if received.message is not None and received.stored is not None:
        background.add_task(inbound.process, secrets, received.message, received.stored)
        if received.stored.ai_paused:
            # Un cliente escribe en un chat pausado: si ya esperó demasiado, la IA lo retoma ahora.
            background.add_task(whatsapp_qr_webhook.sweep_after_message)
    return {"status": received.status}
