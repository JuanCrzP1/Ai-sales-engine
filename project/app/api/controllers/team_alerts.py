"""Avisar al equipo por correo y notificación: lo mismo para todos los canales del motor (WhatsApp, la API del asistente…)."""
from __future__ import annotations

from app.business_config_application.attention import TeamAlerts
from app.infrastructure.business_config import runtime_access
from app.infrastructure.channels.public_url import panel_url
from app.infrastructure.notifications.resend_email import ResendEmailSender
from app.infrastructure.notifications.web_push import WebPushSender
from app.utils.logger import logger


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
