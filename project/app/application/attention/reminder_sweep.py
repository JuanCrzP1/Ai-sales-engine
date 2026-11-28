"""Los recordatorios del equipo avisan cuando llega su hora.

Una revisión busca los recordatorios pendientes que ya llegaron a su hora y, en cada uno:

1. Crea su aviso en la campana, reservándolo de forma atómica (`alert_due`): si otra revisión ya lo tomó o alguien lo marcó hecho justo
   antes, no hace nada. El aviso es para su responsable; sin responsable, o si ya no es del equipo, para todo el equipo.
2. Lo manda como notificación a sus celulares y navegadores (`alerts`); al tocarla se abre la ficha del cliente. Sin correo: el correo
   es para cuando un cliente espera a una persona.

Quién la corre: Vercel cada 15 minutos (con la de la atención humana, `/api/v1/internal/attention/run`) y el tráfico del motor y del
panel (como mucho una vez por minuto por proceso): con el panel abierto, el aviso llega a tiempo.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from app.utils.logger import logger


class ReminderSweep:
    def __init__(
        self,
        *,
        alert_due: Callable[..., list[str]],
        alerts: Callable[[str | None], Any],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._alert_due = alert_due
        self._alerts = alerts
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def run(self) -> int:
        """Cuántos recordatorios avisaron. La notificación de uno que falla no detiene las demás: su aviso ya está en la campana."""
        created = self._alert_due(now=self._clock())
        for notification_id in created:
            try:
                self._alerts(notification_id)
            except Exception as exc:  # noqa: BLE001
                logger.error("recordatorio_sin_notificacion", extra={"error": type(exc).__name__})
        if created:
            logger.info("recordatorios_avisaron", extra={"alerted": len(created)})
        return len(created)
