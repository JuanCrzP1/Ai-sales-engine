"""El seguimiento a los clientes que dejaron de responder: una revisión periódica que envía el mensaje que toca a cada uno.

El negocio lo enciende en Mensajes → Seguimiento y elige los mensajes y sus tiempos (`domain/business_config/follow_up.py`). En cada
revisión, para cada chat de WhatsApp o Telegram en el que el cliente dejó de responder:

1. Mira si toca un seguimiento: el negocio lo tiene encendido, es su horario (si así lo eligió) y ya pasó el tiempo del siguiente.
2. Lo toma de forma atómica (`claim_follow_up`): si otra revisión ya lo tomó, o el cliente escribió justo antes, no hace nada. Así
   ningún cliente recibe el mismo seguimiento dos veces, aunque haya varios servidores.
3. La IA lee el final del chat (`follow_up_reading.py`): si el cliente cerró la conversación («no me interesa», «ya compré»), el
   seguimiento se detiene en ese chat y no se le escribe más. Si la IA no responde, no se envía nada y queda para la próxima revisión.
4. Lo envía por el canal del cliente, queda en la bandeja marcado como seguimiento y en el historial que lee la IA: si el cliente
   responde, el asistente sabe qué se le escribió.

Nunca se escribe a quien lo atiende el equipo (la IA pausada o esperando a una persona), avisó un pago o ya compró, ni en los chats de
prueba. Un mensaje que no salió por el canal no se reintenta: mejor uno de menos que uno repetido.

Quién la corre: Vercel cada 15 minutos (`/api/v1/internal/follow-up/run`, con `CRON_SECRET`) y el tráfico del motor (como mucho una
vez cada pocos minutos por proceso).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.domain.business_config.channels import ChannelSecrets
from app.domain.business_config.conversations import FollowUpCandidate
from app.domain.business_config.engine_policy import MAX_FOLLOW_UP_MINUTES, MIN_FOLLOW_UP_MINUTES
from app.domain.business_config.follow_up import STALE_AFTER, FollowUpPlan, due_step
from app.utils.logger import logger

# Más allá de esto ningún seguimiento puede tocar: el último sale como tarde a los 30 días y, si ya es viejo, no sale.
OLDEST_ACTIVITY = timedelta(minutes=MAX_FOLLOW_UP_MINUTES) + STALE_AFTER
SHORTEST_WAIT = timedelta(minutes=MIN_FOLLOW_UP_MINUTES)


@dataclass(frozen=True)
class FollowUpResult:
    checked: int
    sent: int
    # Ya eran viejos y se saltaron sin enviarlos.
    skipped: int
    # El cliente había cerrado la conversación: el seguimiento se detuvo en ese chat.
    stopped: int


class FollowUpSweep:
    def __init__(
        self,
        *,
        candidates: Callable[..., list[FollowUpCandidate]],
        plan: Callable[[str], FollowUpPlan],
        zone: Callable[[str], ZoneInfo],
        claim: Callable[[FollowUpCandidate, int], bool],
        release: Callable[[FollowUpCandidate], Any],
        stop: Callable[[str, str], Any],
        recent: Callable[[str], list[tuple[str, str]]],
        read: Callable[[str, list[tuple[str, str]], str], bool | None],
        secrets: Callable[[str, str], ChannelSecrets | None],
        send: Callable[[ChannelSecrets, str, str], bool],
        remember: Callable[[str, str, str], Any],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._candidates = candidates
        self._plan = plan
        self._zone = zone
        self._claim = claim
        self._release = release
        self._stop = stop
        self._recent = recent
        self._read = read
        self._secrets = secrets
        self._send = send
        self._remember = remember
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def run(self, *, limit: int = 200) -> FollowUpResult:
        now = self._clock()
        chats = self._candidates(active_since=now - OLDEST_ACTIVITY, quiet_before=now - SHORTEST_WAIT, limit=limit)
        plans: dict[str, FollowUpPlan | None] = {}
        sent = skipped = stopped = 0
        for chat in chats:
            plan = self._business_plan(chat.business_slug, plans)
            if plan is None or not plan.active:
                continue
            try:
                outcome = self._follow_up(chat, plan, now)
            except Exception as exc:  # noqa: BLE001 - un chat con problemas no detiene la revisión de los demás
                logger.error("seguimiento_fallido", extra={"tenant": chat.business_slug, "error": type(exc).__name__})
                continue
            sent += outcome == "sent"
            skipped += outcome == "skipped"
            stopped += outcome == "stopped"
        if sent or skipped or stopped:
            logger.info("seguimientos_revisados", extra={"checked": len(chats), "sent": sent, "skipped": skipped, "stopped": stopped})
        return FollowUpResult(checked=len(chats), sent=sent, skipped=skipped, stopped=stopped)

    def _business_plan(self, slug: str, plans: dict[str, FollowUpPlan | None]) -> FollowUpPlan | None:
        if slug not in plans:
            try:
                plans[slug] = self._plan(slug)
            except Exception as exc:  # noqa: BLE001 - un negocio sin versión publicada no detiene a los demás
                logger.warning("seguimiento_sin_configuracion", extra={"tenant": slug, "error": type(exc).__name__})
                plans[slug] = None
        return plans[slug]

    def _follow_up(self, chat: FollowUpCandidate, plan: FollowUpPlan, now: datetime) -> str:
        """Lo que pasó con este chat: «sent», «skipped», «stopped» o «none»."""
        if plan.business_hours_only and not plan.may_send_now(self._zone(chat.business_slug), now):
            return "none"
        due = due_step(plan, last_customer_at=chat.last_customer_at, sent=chat.sent_since_last_message, now=now)
        if due is None:
            return "none"
        if due.message is None:
            # Ya es viejo: no sale, y la secuencia sigue con los siguientes.
            return "skipped" if self._claim(chat, due.index + 1) else "none"
        secrets = self._secrets(chat.business_slug, chat.channel)
        if secrets is None:
            return "none"  # El canal no está conectado: se intenta en la próxima revisión.
        if not self._claim(chat, due.index + 1):
            return "none"
        decision = self._read(chat.business_slug, self._recent(chat.id), due.message)
        if decision is None:
            self._release(chat)
            return "none"
        if decision is False:
            self._stop(chat.id, "customer")
            logger.info("seguimiento_detenido_por_el_cliente", extra={"tenant": chat.business_slug})
            return "stopped"
        if not self._send(secrets, chat.contact_ref, due.message):
            return "none"  # Queda en la bandeja como «no enviado»; no se reintenta.
        try:
            self._remember(chat.business_slug, chat.contact_ref, due.message)
        except Exception as exc:  # noqa: BLE001 - el mensaje ya salió: la IA no lo verá en su historial, pero el cliente sí lo tiene
            logger.warning("seguimiento_sin_historial", extra={"tenant": chat.business_slug, "error": type(exc).__name__})
        logger.info("seguimiento_enviado", extra={"tenant": chat.business_slug, "channel": chat.channel, "step": due.index + 1})
        return "sent"
