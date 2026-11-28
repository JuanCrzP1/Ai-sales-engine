"""Los recordatorios del equipo: qué hacer con un cliente y cuándo («llamarlo para cerrar», mañana a las 9).

- Cada recordatorio es de un cliente, tiene un texto, una fecha y hora, y un responsable del equipo (o ninguno). Si no se elige, queda
  para quien lo crea.
- Se marca hecho (y se puede volver a abrir) o se borra. Todo el que atiende puede crearlos, marcarlos y borrarlos.
- El panel los agrupa en vencidos, de hoy y próximos con la hora de quien mira; los hechos aparte. Se ven en la ficha del cliente, en
  su tarjeta del tablero (el más próximo) y en la vista «Recordatorios» de Clientes, los míos o los de todo el equipo.
- Se llaman recordatorios, no seguimientos: «Seguimiento» ya es el mensaje automático al cliente que deja de responder.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

MAX_TITLE = 140
MAX_OPEN_PER_CUSTOMER = 20
MAX_LISTED_OPEN = 500
MAX_LISTED_DONE = 100
# Una fecha un poco en el pasado se acepta (el reloj de quien la elige puede ir atrás); una de hace más, no.
PAST_TOLERANCE = timedelta(minutes=10)
MAX_AHEAD = timedelta(days=366 * 2)


class ReminderError(ValueError):
    """Un dato del recordatorio no sirve. `field` dice cuál; el mensaje es para el negocio."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


class _Unset:
    def __repr__(self) -> str:
        return "UNSET"


# El responsable que la petición no trae: queda para quien lo crea.
FOR_ME = _Unset()


@dataclass(frozen=True)
class NewReminder:
    title: str
    due_at: datetime
    # El `user_id` del responsable, None para nadie, o `FOR_ME`.
    assignee_id: str | None | _Unset = FOR_ME

    @classmethod
    def checked(cls, *, title: object, due_at: object, now: datetime, assignee_id: object = FOR_ME) -> NewReminder:
        text = " ".join(str(title or "").split())
        if not text:
            raise ReminderError("title", "Escribe qué hay que hacer.")
        if len(text) > MAX_TITLE:
            raise ReminderError("title", f"Es muy largo (máximo {MAX_TITLE} caracteres).")
        try:
            moment = datetime.fromisoformat(str(due_at or "").strip().replace("Z", "+00:00"))
        except ValueError:
            raise ReminderError("due_at", "Elige la fecha y la hora.") from None
        if moment.tzinfo is None:
            raise ReminderError("due_at", "Elige la fecha y la hora.")
        moment = moment.astimezone(timezone.utc)
        if moment < now - PAST_TOLERANCE:
            raise ReminderError("due_at", "Esa fecha ya pasó: elige una que venga.")
        if moment > now + MAX_AHEAD:
            raise ReminderError("due_at", "Elige una fecha de los próximos dos años.")
        owner: str | None | _Unset = FOR_ME
        if assignee_id is not FOR_ME:
            owner = str(assignee_id or "").strip() or None
        return cls(text, moment, owner)


@dataclass(frozen=True)
class Reminder:
    id: str
    conversation_id: str
    customer_name: str | None
    customer_contact: str
    title: str
    due_at: datetime
    assignee_id: str | None = None
    assignee_label: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    done_at: datetime | None = None
    done_by: str | None = None


@dataclass(frozen=True)
class NextReminder:
    """El recordatorio pendiente más próximo de un cliente, para su tarjeta del tablero."""

    title: str
    due_at: datetime
