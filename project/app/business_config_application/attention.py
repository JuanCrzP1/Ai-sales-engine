"""Atención humana en el panel y avisos al equipo.

- `AttentionService`: los ajustes de Ajustes → Atención humana de cada negocio (solo los de quien pregunta), con el horario de «Mi
  negocio» para mostrarlo, si hay alguien del equipo ahora, y el correo de prueba.
- `PushService`: activar y desactivar las notificaciones en cada navegador o celular, y enviar una de prueba.
- `TeamAlerts`: entrega un aviso (un chat pasó a una persona, la IA retomó un chat) por correo y como notificación. Cada aviso sale
  una sola vez por canal aunque dos procesos lo intenten a la vez, y nunca lanza: un correo que no sale no puede tumbar la atención.

Las pruebas («Probar asistente») nunca mandan correos ni notificaciones: la campana del panel ya las muestra.
"""
from __future__ import annotations

import html
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import AttentionStorage, EmailNotSent, EmailSender, PushSender, PushStorage
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.access import Principal
from app.domain.business_config.attention import (
    AttentionSettings,
    HoursRange,
    hours_from,
    is_open,
    next_opening,
    team_hours,
    validated,
)
from app.domain.business_config.errors import BusinessConfigError, FieldIssue, InvalidFieldsError
from app.domain.business_config.push import PushMessage, validated_subscription

logger = logging.getLogger("attention")

PLAYGROUND_CHANNEL = "prueba"
# Cada cuánto se vuelve a anotar el correo de una cuenta que usa el panel (por proceso).
REMEMBER_EVERY_SECONDS = 10 * 60


def business_hours(configs: BusinessConfigService, tenant_slug: str) -> tuple[HoursRange, ...]:
    """El horario de «Mi negocio» que ven los clientes: el publicado; si nunca se publicó, el del borrador."""
    config = None
    try:
        config = configs.get_published(tenant_slug)
    except BusinessConfigError:
        draft = configs.get_draft(tenant_slug)
        config = draft.config if draft is not None else None
    if config is None:
        return ()
    return hours_from([hours.model_dump(mode="json") for hours in config.identity.opening_hours or []])


def conversation_path(business_slug: str, conversation_id: str | None) -> str:
    """La ruta del panel que abre ese chat (la misma que usa la campana)."""
    base = f"/negocios/{quote(business_slug)}/conversaciones"
    return f"{base}?c={quote(conversation_id)}" if conversation_id else base


@dataclass(frozen=True)
class AttentionView:
    settings: AttentionSettings
    business_hours: tuple[HoursRange, ...]
    # Adónde llega el correo si el negocio no escribe otro: los correos de las cuentas dueñas.
    account_emails: list[str]
    # La plataforma tiene el correo de avisos activado (si no, el panel lo dice en lugar de prometer correos).
    email_available: bool
    team_available_now: bool
    next_opening: datetime | None


class AttentionService:
    def __init__(
        self,
        storage: AttentionStorage,
        access: BusinessAccess,
        configs: BusinessConfigService,
        email: EmailSender | None = None,
    ) -> None:
        self._storage = storage
        self._access = access
        self._configs = configs
        self._email = email
        self._remembered: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def view(self, principal: Principal, business: str, *, now: datetime | None = None) -> AttentionView:
        self._access.require(principal, business)
        settings = self._storage.attention_settings(business)
        hours = business_hours(self._configs, business)
        now = now or datetime.now(timezone.utc)
        zone, effective = ZoneInfo(settings.timezone), team_hours(settings, hours)
        available = is_open(effective, zone, now)
        return AttentionView(
            settings=settings,
            business_hours=hours,
            account_emails=self._storage.owner_emails(business) or ([principal.email] if principal.email else []),
            email_available=bool(self._email is not None and self._email.configured),
            team_available_now=available,
            next_opening=None if available else next_opening(effective, zone, now),
        )

    def save(self, principal: Principal, business: str, payload: dict[str, Any], *, now: datetime | None = None) -> AttentionView:
        self._access.require(principal, business)
        settings = validated(
            hours_mode=payload.get("hours_mode"),
            team_hours=payload.get("team_hours"),
            timezone_name=payload.get("timezone"),
            reply_minutes=payload.get("reply_minutes"),
            resume_after_minutes=payload.get("resume_after_minutes"),
            email_enabled=payload.get("email_enabled"),
            email_to=payload.get("email_to"),
        )
        self._storage.save_attention_settings(business, settings)
        logger.info("atencion_humana_guardada", extra={"tenant": business, "hours_mode": settings.hours_mode})
        return self.view(principal, business, now=now)

    def send_test_email(self, principal: Principal, business: str) -> list[str]:
        """Envía un correo de prueba adonde llegarían los avisos de este negocio y dice a quién."""
        self._access.require(principal, business)
        if self._email is None or not self._email.configured:
            raise EmailNotSent("El correo de avisos aún no está activado en la plataforma.")
        settings = self._storage.attention_settings(business)
        recipients = [settings.email_to] if settings.email_to else (self._storage.owner_emails(business) or ([principal.email] if principal.email else []))
        if not recipients:
            raise EmailNotSent("No hay un correo adónde enviarlo. Escribe uno en «Avisos por correo».")
        name = next((summary.name for summary in self._access.list_for(principal) if summary.slug == business), business)
        subject, text, body = alert_email(
            title="Así te llegarán los avisos", business_name=name, detail="Este es un correo de prueba de la atención humana.",
            link=None, footer_business=name,
        )
        self._email.send(to=recipients, subject=subject, html=body, text=text)
        return recipients

    def remember_account(self, principal: Principal, *, force: bool = False) -> None:
        """Anota el correo de la cuenta en sus negocios, para avisarle por correo. Como mucho cada 10 minutos por proceso."""
        if principal.local_operator or not principal.email:
            return
        now = time.monotonic()
        with self._lock:
            seen = self._remembered.get(principal.user_id)
            if not force and seen is not None and seen[0] == principal.email and now - seen[1] < REMEMBER_EVERY_SECONDS:
                return
            self._remembered[principal.user_id] = (principal.email, now)
        try:
            self._storage.remember_email(principal.user_id, principal.email)
        except Exception:  # noqa: BLE001 - anotar el correo nunca puede tumbar una petición del panel
            logger.exception("correo_de_la_cuenta_no_anotado")


class PushService:
    def __init__(self, storage: PushStorage, sender: PushSender | None = None) -> None:
        self._storage = storage
        self._sender = sender

    def public_key(self) -> str:
        return self._storage.vapid_public_key()

    def status(self, principal: Principal, endpoint: str | None) -> bool:
        return bool(endpoint) and self._storage.is_subscribed(principal.user_id, str(endpoint))

    def subscribe(self, principal: Principal, payload: dict[str, Any]) -> None:
        keys = payload.get("keys") if isinstance(payload.get("keys"), dict) else {}
        subscription = validated_subscription(
            principal.user_id, endpoint=payload.get("endpoint"), p256dh=keys.get("p256dh"), auth=keys.get("auth"), device=payload.get("device"),
        )
        self._storage.subscribe(subscription)
        logger.info("notificaciones_activadas")

    def unsubscribe(self, principal: Principal, endpoint: str) -> bool:
        return self._storage.unsubscribe(principal.user_id, str(endpoint or ""))

    def send_test(self, principal: Principal, endpoint: str) -> None:
        """Una notificación de prueba a este navegador, para ver que llega."""
        if self._sender is None:
            raise InvalidFieldsError("Las notificaciones no están disponibles.", [])
        mine = [item for item in self._storage.subscriptions_for([principal.user_id]) if item.endpoint == endpoint]
        if not mine:
            raise InvalidFieldsError("Activa primero las notificaciones en este navegador.", [FieldIssue("endpoint", "Este navegador no las tiene activadas.")])
        outcome = self._sender.send(
            mine[0], PushMessage(title="Notificaciones activadas", body="Así te avisaremos cuando un cliente necesite a una persona.", url="/", tag="prueba")
        )
        if outcome.status == "gone":
            self._storage.forget(endpoint)
        if outcome.status != "sent":
            raise InvalidFieldsError("La notificación de prueba no salió. Vuelve a activarlas.", [])


# ---------------------------------------------------------------------------------------------------------- avisos


def alert_email(*, title: str, business_name: str, detail: str | None, link: str | None, footer_business: str) -> tuple[str, str, str]:
    """El correo de un aviso: asunto, texto plano y HTML. Todo lo que viene del cliente se escapa."""
    subject = f"{title} · {business_name}"
    text_lines = [title, "", f"Negocio: {business_name}"]
    if detail:
        text_lines += ["", f"«{detail}»"]
    if link:
        text_lines += ["", f"Abrir el chat: {link}"]
    text_lines += ["", f"Recibes este correo porque atiendes {footer_business}. Cámbialo en Ajustes → Atención humana."]
    esc = html.escape
    quote_block = (
        f'<p style="margin:16px 0;padding:12px 16px;background:#f4f6f8;border-left:3px solid #16a34a;border-radius:6px;color:#1f2937">'
        f"«{esc(detail)}»</p>"
        if detail
        else ""
    )
    button = (
        f'<p style="margin:24px 0"><a href="{esc(link, quote=True)}" style="display:inline-block;background:#16a34a;color:#ffffff;'
        f'text-decoration:none;padding:12px 20px;border-radius:8px;font-weight:600">Abrir el chat</a></p>'
        if link
        else ""
    )
    body = (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#111827">'
        '<p style="margin:0 0 16px;font-size:13px;color:#6b7280;letter-spacing:.02em">AI SALES ENGINE</p>'
        f'<h1 style="margin:0 0 8px;font-size:20px;line-height:1.3">{esc(title)}</h1>'
        f'<p style="margin:0;color:#4b5563">{esc(business_name)}</p>'
        f"{quote_block}{button}"
        '<hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">'
        f'<p style="margin:0;font-size:12px;color:#6b7280">Recibes este correo porque atiendes {esc(footer_business)}. '
        "Cámbialo en Ajustes → Atención humana.</p></div>"
    )
    return subject, "\n".join(text_lines), body


class TeamAlerts:
    def __init__(
        self,
        storage: AttentionStorage,
        *,
        push_storage: PushStorage | None = None,
        email: EmailSender | None = None,
        push: PushSender | None = None,
        panel_url: str = "",
    ) -> None:
        self._storage = storage
        self._push_storage = push_storage
        self._email = email
        self._push = push
        self._panel_url = panel_url.rstrip("/")

    def deliver(self, notification_id: str | None) -> None:
        """Avisa al equipo por correo (solo cuando un chat pasa a una persona) y por notificación. Nunca lanza."""
        if not notification_id:
            return
        try:
            alert = self._storage.alert(notification_id)
        except Exception:  # noqa: BLE001
            logger.exception("aviso_no_encontrado")
            return
        if alert.channel == PLAYGROUND_CHANNEL:
            return
        path = conversation_path(alert.business_slug, alert.conversation_id)
        if alert.kind == "handoff":
            self._send_email(alert, f"{self._panel_url}{path}" if self._panel_url else None)
        self._send_push(alert, path)

    def _send_email(self, alert: Any, link: str | None) -> None:
        try:
            settings = self._storage.attention_settings(alert.business_slug)
            if not settings.email_enabled:
                return
            if self._email is None or not self._email.configured:
                self._skip(alert.notification_id, "email", "correo no activado en la plataforma")
                return
            recipients = [settings.email_to] if settings.email_to else self._storage.owner_emails(alert.business_slug)
            if not recipients:
                self._skip(alert.notification_id, "email", "sin correo de destino")
                return
            if not self._storage.claim_delivery(alert.notification_id, "email"):
                return
            subject, text, body = alert_email(
                title=alert.title, business_name=alert.business_name, detail=alert.body, link=link, footer_business=alert.business_name
            )
            try:
                self._email.send(to=recipients, subject=subject, html=body, text=text, idempotency_key=f"aviso-{alert.notification_id}")
            except EmailNotSent as exc:
                self._storage.finish_delivery(alert.notification_id, "email", "failed", str(exc))
                logger.warning("aviso_por_correo_fallido", extra={"tenant": alert.business_slug, "error": str(exc)})
                return
            self._storage.finish_delivery(alert.notification_id, "email", "sent")
            logger.info("aviso_por_correo_enviado", extra={"tenant": alert.business_slug})
        except Exception as exc:  # noqa: BLE001 - el correo nunca tumba la atención
            logger.error("aviso_por_correo_error", extra={"tenant": alert.business_slug, "error": type(exc).__name__})

    def _send_push(self, alert: Any, path: str) -> None:
        if self._push is None or self._push_storage is None:
            return
        try:
            subscriptions = self._push_storage.subscriptions_for(self._storage.member_ids(alert.business_slug))
            if not subscriptions or not self._storage.claim_delivery(alert.notification_id, "push"):
                return
            body = f"{alert.business_name}: {alert.body}" if alert.body else alert.business_name
            message = PushMessage(title=alert.title, body=body[:180], url=path, tag=alert.conversation_id or alert.notification_id)
            sent = 0
            for subscription in subscriptions:
                outcome = self._push.send(subscription, message)
                if outcome.status == "sent":
                    sent += 1
                    self._push_storage.mark_delivered(subscription.endpoint)
                elif outcome.status == "gone":
                    self._push_storage.forget(subscription.endpoint)
            status = "sent" if sent else "failed"
            self._storage.finish_delivery(alert.notification_id, "push", status, f"{sent} de {len(subscriptions)} dispositivos")
            logger.info("aviso_por_notificacion", extra={"tenant": alert.business_slug, "sent": sent, "devices": len(subscriptions)})
        except Exception as exc:  # noqa: BLE001
            logger.error("aviso_por_notificacion_error", extra={"tenant": alert.business_slug, "error": type(exc).__name__})

    def _skip(self, notification_id: str, channel: str, reason: str) -> None:
        if self._storage.claim_delivery(notification_id, channel):
            self._storage.finish_delivery(notification_id, channel, "skipped", reason)
