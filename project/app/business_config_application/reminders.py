"""Los recordatorios del equipo en el panel. Cada usuario solo llega a sus negocios; todo el que atiende puede crearlos, marcarlos y
borrarlos (son su herramienta de trabajo con los clientes)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import ReminderStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.reminders import FOR_ME, NewReminder, Reminder


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ReminderService:
    def __init__(self, storage: ReminderStorage, access: BusinessAccess, *, clock: Callable[[], datetime] = _now) -> None:
        self._storage = storage
        self._access = access
        self._clock = clock

    def reminders(self, principal: Principal, business: str, *, done: bool = False, mine: bool = False) -> list[Reminder]:
        """Los pendientes (o los hechos) del negocio; con `mine`, solo los de quien mira."""
        self._access.require(principal, business)
        return self._storage.reminders(business, done=done, assignee_id=principal.user_id if mine else None)

    def create(self, principal: Principal, business: str, conversation_id: str, *, title: object, due_at: object, assignee_id: object = FOR_ME) -> Reminder:
        """Sin `assignee_id`, queda para quien lo crea (si es del equipo). `ReminderError` si un dato no sirve."""
        self._access.require(principal, business)
        reminder = NewReminder.checked(title=title, due_at=due_at, now=self._clock(), assignee_id=assignee_id)
        return self._storage.create_reminder(business, conversation_id, reminder, by_user=principal.user_id, by=principal.label)

    def mark(self, principal: Principal, business: str, reminder_id: str, *, done: bool) -> Reminder:
        self._access.require(principal, business)
        return self._storage.set_reminder_done(business, reminder_id, done, by=principal.label)

    def delete(self, principal: Principal, business: str, reminder_id: str) -> None:
        self._access.require(principal, business)
        self._storage.delete_reminder(business, reminder_id)
