"""El seguimiento a un cliente que dejó de responder: cuándo sale cada mensaje (Mensajes → Seguimiento, `messages.follow_up`).

El negocio elige hasta 5 mensajes, cada uno con su tiempo contado desde el último mensaje del cliente («1 hora después», «al día
siguiente», «a los 3 días»). Los envía la plataforma tal cual, no la IA. Las reglas:

- **Solo a quien dejó de responder:** el último mensaje del chat es del negocio y el del cliente quedó atrás. Si el cliente vuelve a
  escribir, la secuencia vuelve a empezar desde el primero cuando quede otra vez en silencio.
- **Nunca dos a la vez:** si se juntan varios (el negocio estaba cerrado, la revisión no corrió), sale solo el más reciente.
- **Nada viejo:** un mensaje que debía salir hace más de `STALE_AFTER` no sale (por ejemplo, al encender el seguimiento no se le
  escribe a quien dejó de responder hace semanas); la secuencia sigue con los siguientes.
- **En el horario del negocio**, si así lo eligió (el de Mi negocio). Sin horario escrito, a cualquier hora.

Quién lo envía, cuándo se detiene (el cliente compra, avisa un pago, pide una persona, el equipo lo atiende o dice que no le
interesa) y cómo se evita enviarlo dos veces está en `application/follow_up/follow_up_sweep.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.business_config.attention import HoursRange, hours_from, is_open

# Un seguimiento que debía salir hace más de esto ya no sale: tres días alcanzan para un fin de semana largo con el negocio cerrado.
STALE_AFTER = timedelta(days=3)
# Cómo se marca en la bandeja un mensaje de seguimiento (la «intención» del mensaje del asistente).
FOLLOW_UP_INTENT = "follow_up"


@dataclass(frozen=True)
class FollowUpStepPlan:
    after: timedelta
    message: str


@dataclass(frozen=True)
class FollowUpPlan:
    """Lo publicado del seguimiento de un negocio, con su horario."""

    enabled: bool = False
    business_hours_only: bool = True
    steps: tuple[FollowUpStepPlan, ...] = ()
    business_hours: tuple[HoursRange, ...] = ()

    @property
    def active(self) -> bool:
        return self.enabled and bool(self.steps)

    def may_send_now(self, zone: ZoneInfo, now: datetime) -> bool:
        """Si a esta hora puede salir un seguimiento: siempre, o dentro del horario del negocio si así lo eligió."""
        return not self.business_hours_only or is_open(self.business_hours, zone, now)


@dataclass(frozen=True)
class FollowUpDue:
    """El seguimiento que toca: su posición en la secuencia y su texto, o `message=None` si ya es viejo y se salta sin enviarlo."""

    index: int
    message: str | None


def published_follow_up(sections: dict) -> FollowUpPlan:
    """Lee lo compilado de la versión publicada (`config.follow_up` y el horario de `config.profile.opening_hours`)."""
    config = sections.get("config") if isinstance(sections, dict) and isinstance(sections.get("config"), dict) else {}
    raw = config.get("follow_up") if isinstance(config.get("follow_up"), dict) else {}
    profile = config.get("profile") if isinstance(config.get("profile"), dict) else {}
    steps = tuple(
        FollowUpStepPlan(timedelta(minutes=int(step["after_minutes"])), str(step["message"]).strip())
        for step in raw.get("steps") or []
        if isinstance(step, dict) and str(step.get("message") or "").strip() and isinstance(step.get("after_minutes"), int)
    )
    return FollowUpPlan(
        enabled=raw.get("enabled") is True,
        business_hours_only=raw.get("business_hours_only") is not False,
        steps=steps,
        business_hours=hours_from(profile.get("opening_hours")),
    )


def due_step(plan: FollowUpPlan, *, last_customer_at: datetime, sent: int, now: datetime) -> FollowUpDue | None:
    """El seguimiento que toca ahora, o None si todavía no toca ninguno. `sent`: cuántos de la secuencia ya pasaron desde ese
    último mensaje del cliente."""
    due = [index for index in range(max(sent, 0), len(plan.steps)) if last_customer_at + plan.steps[index].after <= now]
    if not due:
        return None
    latest = due[-1]
    if now - (last_customer_at + plan.steps[latest].after) > STALE_AFTER:
        return FollowUpDue(latest, None)
    return FollowUpDue(latest, plan.steps[latest].message)
