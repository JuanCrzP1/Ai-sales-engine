"""La IA retoma sola los chats que nadie del equipo atendió a tiempo.

Cada negocio elige cuánto puede esperar un cliente (Configuración → Atención humana; por defecto 30 minutos, o nunca). Una revisión busca
los chats con la IA pausada y un cliente esperando desde antes de ese tiempo y, en cada uno:

1. Reserva el chat de forma atómica (`resume_waiting`): si otra revisión ya lo tomó o alguien del equipo respondió, no hace nada.
2. Le pide disculpas al cliente y el asistente responde lo que escribió mientras esperaba (`continue_after_resume`).
3. Avisa al equipo (campana y notificación). El chat sigue esperando a una persona: la IA solo atiende mientras tanto.

Quién la corre: Vercel cada 15 minutos (`/api/v1/internal/attention/run`, con `CRON_SECRET`), el tráfico del motor y del panel (como
mucho una vez por minuto por proceso) y cada mensaje que llega a un chat pausado. Nada espera en una función abierta.
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.domain.business_config.attention import RESUME_MINUTES, AttentionSettings, resume_due
from app.domain.business_config.assistant_api import API_CHANNEL
from app.domain.business_config.channels import WHATSAPP, WhatsAppSecrets
from app.domain.business_config.conversations import WaitingChat
from app.utils.logger import logger

# Los canales en los que la IA retoma: por WhatsApp pide disculpas y responde lo pendiente; por la API (Leona, una web) no hay por
# dónde escribirle al cliente, así que solo vuelve a atender y responde su próximo mensaje.
RESUMABLE_CHANNELS = (WHATSAPP, API_CHANNEL)
# Ningún negocio puede elegir menos que esto: los chats que esperan menos ni se consultan.
SHORTEST_WAIT = timedelta(minutes=min(RESUME_MINUTES))


@dataclass(frozen=True)
class SweepResult:
    checked: int
    resumed: int


class ResumeSweep:
    def __init__(
        self,
        *,
        waiting: Callable[..., list[WaitingChat]],
        settings: Callable[[str], AttentionSettings],
        resume: Callable[..., str | None],
        pending: Callable[..., str],
        secrets: Callable[[str], WhatsAppSecrets | None],
        continue_chat: Callable[[WhatsAppSecrets, str, str, str], Any],
        alerts: Callable[[str | None], Any],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._waiting = waiting
        self._settings = settings
        self._resume = resume
        self._pending = pending
        self._secrets = secrets
        self._continue = continue_chat
        self._alerts = alerts
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def run(self, *, limit: int = 50) -> SweepResult:
        now = self._clock()
        chats = self._waiting(waiting_before=now - SHORTEST_WAIT, limit=limit)
        settings: dict[str, AttentionSettings | None] = {}
        resumed = 0
        for chat in chats:
            if chat.channel not in RESUMABLE_CHANNELS:
                continue
            if chat.business_slug not in settings:
                try:
                    settings[chat.business_slug] = self._settings(chat.business_slug)
                except Exception as exc:  # noqa: BLE001 - un negocio con problemas no detiene la revisión de los demás
                    logger.warning("atencion_ajustes_no_disponibles", extra={"tenant": chat.business_slug, "error": type(exc).__name__})
                    settings[chat.business_slug] = None
            chosen = settings[chat.business_slug]
            if chosen is None or not resume_due(chosen, chat.waiting_since, now):
                continue
            if self._resume_one(chat, chosen, now):
                resumed += 1
        if resumed:
            logger.info("ia_retomo_chats", extra={"checked": len(chats), "resumed": resumed})
        return SweepResult(checked=len(chats), resumed=resumed)

    def _resume_one(self, chat: WaitingChat, chosen: AttentionSettings, now: datetime) -> bool:
        minutes = int(chosen.resume_after_minutes or 0)
        try:
            pending = self._pending(chat.id, since=chat.waiting_since)
            notification = self._resume(chat.id, waiting_before=now - timedelta(minutes=minutes), minutes=minutes)
        except Exception as exc:  # noqa: BLE001
            logger.error("ia_no_pudo_retomar", extra={"tenant": chat.business_slug, "error": type(exc).__name__})
            return False
        if notification is None:
            return False  # Otra revisión lo tomó, o alguien del equipo respondió justo antes.
        try:
            if chat.channel != WHATSAPP:
                pass  # Por la API no hay por dónde escribirle: la IA responde su próximo mensaje.
            elif (secrets := self._secrets(chat.business_slug)) is None:
                logger.warning("ia_retomo_sin_whatsapp", extra={"tenant": chat.business_slug})
            else:
                self._continue(secrets, chat.id, chat.contact_ref, pending)
        except Exception as exc:  # noqa: BLE001 - el chat ya es de la IA: el siguiente mensaje del cliente lo responde
            logger.error("ia_retomo_sin_responder", extra={"tenant": chat.business_slug, "error": type(exc).__name__})
        self._alerts(notification)
        logger.info("ia_retomo_chat", extra={"tenant": chat.business_slug, "minutes": minutes})
        return True


class Throttle:
    """Deja correr algo como mucho una vez cada `seconds` por proceso, y nunca dos a la vez."""

    def __init__(self, seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._seconds = seconds
        self._clock = clock
        self._last: float | None = None
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        with self._lock:
            now = self._clock()
            if self._last is not None and now - self._last < self._seconds:
                return False
            self._last = now
            return True
