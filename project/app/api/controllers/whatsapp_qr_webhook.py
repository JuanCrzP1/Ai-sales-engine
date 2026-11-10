"""Webhook de WhatsApp por código QR (uazapi): recibe los mensajes de los clientes de cada negocio y responde con su asistente.

Cada negocio tiene su propia ruta, `/channels/whatsapp/{webhook_id}`, con un identificador secreto que registra el panel al conectar.
Además, uazapi manda el token de la instancia en cada aviso: si viene y no es el del negocio, se rechaza.

- Solo se responden mensajes de texto de un cliente en un chat individual: ni grupos, ni lo que escribe el negocio desde su
  teléfono, ni lo que envió la propia API (uazapi ya los excluye, y aquí se comprueba otra vez).
- Un mensaje repetido (mismo identificador) se responde una sola vez.
- Se contesta a uazapi enseguida y la respuesta se envía después: el asistente puede tardar unos segundos.
- Cada intercambio queda en la bandeja de Conversaciones, con los datos de pago ocultos.
"""
from __future__ import annotations

import hmac
import threading
import time
from collections import OrderedDict

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.application.runtime import published_sections
from app.domain.business_config.channels import WHATSAPP, ChannelError, IncomingMessage, WhatsAppSecrets
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.errors import BusinessConfigError
from app.domain.business_config.payment_data import redact_payment_values
from app.infrastructure.business_config import runtime_access
from app.infrastructure.channels.uazapi import UazapiClient, connection_event, parse_incoming
from app.models import Tenant
from app.services.ai_service import AIService
from app.utils.logger import logger

router = APIRouter(prefix="/channels", tags=["WhatsApp QR"])

MIN_WEBHOOK_ID = 24
SEEN_SECONDS = 600
SEEN_MAX = 5000


class _SeenMessages:
    """Los mensajes ya atendidos en este proceso, para no responder dos veces el mismo (uazapi puede avisar más de una vez)."""

    def __init__(self) -> None:
        self._items: OrderedDict[str, float] = OrderedDict()
        self._lock = threading.Lock()

    def first_time(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            while self._items and (len(self._items) > SEEN_MAX or next(iter(self._items.values())) < now - SEEN_SECONDS):
                self._items.popitem(last=False)
            if key in self._items:
                return False
            self._items[key] = now
            return True


_seen = _SeenMessages()


def _connection(webhook_id: str) -> WhatsAppSecrets:
    if len(webhook_id) < MIN_WEBHOOK_ID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    try:
        secrets = runtime_access.whatsapp_for_webhook(webhook_id)
    except BusinessConfigError as exc:
        logger.error("whatsapp_qr_almacen_no_disponible", extra={"error": type(exc).__name__})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No disponible") from exc
    if secrets is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    return secrets


@router.post("/whatsapp/{webhook_id}")
async def receive_whatsapp_qr(webhook_id: str, request: Request, background: BackgroundTasks) -> dict[str, str]:
    secrets = _connection(webhook_id)
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuerpo no válido") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuerpo no válido")
    token = payload.get("token")
    if token is not None and not hmac.compare_digest(str(token), secrets.instance_token):
        logger.warning("whatsapp_qr_rechazado", extra={"tenant": secrets.tenant_slug, "reason": "token_distinto"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    connection = connection_event(payload)
    if connection is not None:
        runtime_access.set_whatsapp_status(secrets.tenant_slug, connection.status, phone=connection.phone, profile_name=connection.profile_name)
        return {"status": "ok"}

    message = parse_incoming(payload)
    if message is None:
        return {"status": "ignored"}
    if not _seen.first_time(f"{secrets.tenant_slug}:{message.message_id}"):
        return {"status": "duplicate"}
    background.add_task(answer_message, secrets, message)
    return {"status": "accepted"}


def answer_message(secrets: WhatsAppSecrets, message: IncomingMessage, *, service: AIService | None = None, client: UazapiClient | None = None) -> None:
    """Responde con el asistente del negocio, envía la respuesta por su servidor y guarda el intercambio en la bandeja."""
    slug = secrets.tenant_slug
    tenant = Tenant(name=slug, slug=slug)
    reply, _ai_used, metadata = (service or AIService()).generate_business_reply(
        tenant=tenant,
        bot_config=None,
        user_message=message.text,
        user_id=message.phone,
        conversation_history=[],
        faq_results=[],
        yaml_config=None,
        include_metadata=True,
    )
    reply = str(reply or "").strip()
    if not reply:
        return
    try:
        (client or UazapiClient(secrets.server_url)).send_text(secrets.instance_token, message.phone, reply)
    except ChannelError as exc:
        logger.error("whatsapp_qr_envio_fallido", extra={"tenant": slug, "error": str(exc)})
        return
    logger.info("whatsapp_qr_respuesta", extra={"tenant": slug})
    _record(secrets, message, reply, metadata if isinstance(metadata, dict) else {})


def _record(secrets: WhatsAppSecrets, message: IncomingMessage, reply: str, metadata: dict) -> None:
    """La bandeja no puede tumbar la respuesta: si falla, se registra el tipo de error, nunca el contenido."""
    try:
        try:
            sections = published_sections(secrets.tenant_slug)
        except Exception:  # noqa: BLE001 - sin lo publicado no hay datos de pago que ocultar
            sections = {}
        intent = str(metadata.get("intent") or "").strip() or None
        runtime_access.record_conversation(
            secrets.tenant_slug,
            channel=WHATSAPP,
            contact_ref=message.phone,
            contact_name=message.contact_name,
            messages=[
                NewMessage("customer", redact_payment_values(message.text, sections)),
                NewMessage("assistant", redact_payment_values(reply, sections), intent),
            ],
            handoff=bool(metadata.get("handoff")),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("whatsapp_qr_conversacion_no_guardada", extra={"tenant": secrets.tenant_slug, "error": type(exc).__name__})
