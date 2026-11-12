"""Webhook de WhatsApp por código QR (uazapi): recibe los avisos de la instancia de cada negocio.

Cada negocio tiene su propia ruta, `/channels/whatsapp/{webhook_id}`, con un identificador secreto que registra el panel al conectar.
Además, solo cuenta lo que trae el token de la instancia del negocio (uazapi lo incluye en cada aviso).

La ruta solo recibe y contesta enseguida; lo que pasa con cada mensaje (guardarlo en vivo, entenderlo, responder o pasarlo a una
persona) está en `app/application/channels/whatsapp_inbound.py`. Lo lento (entender un archivo y responder) se hace después de
contestarle a uazapi.
"""
from __future__ import annotations

import hmac
import os
import threading
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.application.attention.resume_sweep import ResumeSweep, SweepResult, Throttle
from app.application.channels.whatsapp_inbound import WhatsAppInbound
from app.application.runtime import published_sections
from app.application.runtime.business_ai import business_usage_recorder, load_business_ai
from app.business_config_application.attention import TeamAlerts
from app.domain.business_config.channels import WhatsAppSecrets
from app.domain.business_config.errors import BusinessConfigError
from app.infrastructure.ai.media_interpreter import OpenRouterMediaInterpreter
from app.infrastructure.business_config import runtime_access
from app.infrastructure.channels import uazapi
from app.infrastructure.channels.public_url import panel_url
from app.infrastructure.channels.uazapi import UazapiClient
from app.infrastructure.notifications.resend_email import ResendEmailSender
from app.infrastructure.notifications.web_push import WebPushSender
from app.models import Tenant
from app.services.ai_service import AIService
from app.utils.logger import logger

router = APIRouter(prefix="/channels", tags=["WhatsApp QR"])

MIN_WEBHOOK_ID = 24


def answer_with_assistant(slug: str, phone: str, text: str) -> tuple[str, dict]:
    """El asistente del negocio, con lo publicado y su clave de IA. Su memoria de cada cliente la guarda el motor."""
    reply, _ai_used, metadata = AIService().generate_business_reply(
        tenant=Tenant(name=slug, slug=slug),
        bot_config=None,
        user_message=text,
        user_id=phone,
        conversation_history=[],
        faq_results=[],
        yaml_config=None,
        include_metadata=True,
    )
    return str(reply or ""), metadata if isinstance(metadata, dict) else {}


def now() -> datetime:
    """La hora del motor (las pruebas la fijan para no depender del reloj)."""
    return datetime.now(timezone.utc)


def deliver_alert(notification_id: str | None) -> None:
    """Avisa al equipo por correo y notificación. Nunca lanza: el aviso de la campana ya quedó guardado."""
    if not notification_id:
        return
    try:
        attention, push = runtime_access.alert_stores()
        alerts = TeamAlerts(attention, push_storage=push, email=ResendEmailSender(), push=WebPushSender(push.vapid_keys), panel_url=panel_url())
        alerts.deliver(notification_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("aviso_al_equipo_fallido", extra={"error": type(exc).__name__})


def _business_key(slug: str) -> str | None:
    credentials = load_business_ai(slug)
    return credentials.api_key if credentials else None


class _Conversations:
    """La bandeja vista desde el motor: `runtime_access`, su única puerta al almacén."""

    append = staticmethod(runtime_access.append_conversation_message)
    update_entry = staticmethod(runtime_access.update_conversation_entry)
    set_typing = staticmethod(runtime_access.set_conversation_typing)
    request_handoff = staticmethod(runtime_access.request_conversation_handoff)
    ai_paused = staticmethod(runtime_access.conversation_ai_paused)
    team_replied = staticmethod(runtime_access.conversation_team_replied)


def build_inbound() -> WhatsAppInbound:
    return WhatsAppInbound(
        conversations=_Conversations(),
        server=UazapiClient,
        responder=answer_with_assistant,
        media=OpenRouterMediaInterpreter(),
        api_key=_business_key,
        usage=business_usage_recorder,
        sections=published_sections,
        set_status=runtime_access.set_whatsapp_status,
        mark_delivery=runtime_access.mark_conversation_delivery,
        attention=runtime_access.attention_settings,
        alerts=deliver_alert,
        clock=lambda: now(),
    )


# --------------------------------------------------------------------------- la IA retoma lo que nadie atendió


def build_sweep() -> ResumeSweep:
    inbound = build_inbound()
    return ResumeSweep(
        waiting=runtime_access.waiting_chats,
        settings=runtime_access.attention_settings,
        resume=runtime_access.resume_waiting_chat,
        pending=runtime_access.pending_customer_text,
        secrets=runtime_access.whatsapp_secrets,
        continue_chat=inbound.continue_after_resume,
        alerts=deliver_alert,
        clock=lambda: now(),
    )


_SWEEPING = threading.Lock()
# Después de un mensaje a un chat pausado, como mucho una revisión cada 5 s; con el tráfico, una por minuto (por proceso).
_AFTER_MESSAGE = Throttle(5)
_ON_TRAFFIC = Throttle(60)


def run_resume_sweep() -> SweepResult | None:
    """Una revisión de los chats que esperan. Nunca dos a la vez en el mismo proceso; nunca lanza."""
    if not _SWEEPING.acquire(blocking=False):
        return None
    try:
        return build_sweep().run()
    except Exception as exc:  # noqa: BLE001 - la revisión nunca tumba a quien la disparó
        logger.error("revision_de_atencion_fallida", extra={"error": type(exc).__name__})
        return None
    finally:
        _SWEEPING.release()


def sweep_after_message() -> None:
    if _AFTER_MESSAGE.acquire():
        run_resume_sweep()


def traffic_sweep_enabled() -> bool:
    """En Vercel siempre; en este equipo, si el lanzador lo pide (`ATTENTION_SWEEP_ON_TRAFFIC=1`). En las pruebas, no."""
    return bool(os.getenv("VERCEL")) or str(os.getenv("ATTENTION_SWEEP_ON_TRAFFIC") or "").strip() == "1"


def sweep_on_traffic() -> None:
    if traffic_sweep_enabled() and _ON_TRAFFIC.acquire():
        run_resume_sweep()


# Los lectores de los avisos de uazapi: la ruta los pasa para que el flujo no dependa de cómo los manda uazapi.
_UAZAPI = SimpleNamespace(
    connection_event=uazapi.connection_event,
    parse_receipt=uazapi.parse_receipt,
    parse_own_message=uazapi.parse_own_message,
    parse_incoming=uazapi.parse_incoming,
)


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
    # Solo cuenta lo que trae el token de la instancia de este negocio (uazapi lo incluye en cada aviso).
    token = payload.get("token")
    if not isinstance(token, str) or not hmac.compare_digest(token, secrets.instance_token):
        logger.warning("whatsapp_qr_rechazado", extra={"tenant": secrets.tenant_slug, "reason": "token_distinto"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    inbound = build_inbound()
    received = inbound.receive(secrets, payload, parse=_UAZAPI)
    if received.message is not None and received.stored is not None:
        background.add_task(inbound.process, secrets, received.message, received.stored)
        if received.stored.ai_paused:
            # Un cliente escribe en un chat pausado: si ya esperó demasiado, la IA lo retoma ahora.
            background.add_task(sweep_after_message)
    return {"status": received.status}
