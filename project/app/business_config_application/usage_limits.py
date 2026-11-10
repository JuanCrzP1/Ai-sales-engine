"""Hace cumplir los límites de uso (`app.domain.business_config.usage_limits`) con un contador compartido.

En la nube el contador vive en la base (`rate_limits`), porque cada petición puede caer en una instancia distinta. La API local,
que es un solo proceso, puede usar `MemoryUsageCounter`.
"""
from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timezone

from app.business_config_application.ports import UsageCounter
from app.domain.business_config.access import Principal
from app.domain.business_config.errors import UsageLimitExceededError
from app.domain.business_config.usage_limits import (
    AI_KEY_CHECKS_PER_USER,
    PLAYGROUND_PER_BUSINESS,
    PLAYGROUND_PER_USER,
    UsageLimit,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UsageGuard:
    def __init__(self, counter: UsageCounter, *, clock: Callable[[], datetime] = _utc_now) -> None:
        self._counter = counter
        self._clock = clock

    def spend(self, limit: UsageLimit, subject: str) -> None:
        """Cuenta un uso de `subject` (un usuario o un negocio) y falla si con él supera el límite."""
        now = int(self._clock().timestamp())
        start = now - now % limit.window_seconds
        total = self._counter.hit(f"{limit.name}:{subject}", datetime.fromtimestamp(start, timezone.utc))
        if total > limit.limit:
            raise UsageLimitExceededError(start + limit.window_seconds - now)

    def playground_message(self, user: Principal, tenant_slug: str) -> None:
        self.spend(PLAYGROUND_PER_USER, user.user_id)
        self.spend(PLAYGROUND_PER_BUSINESS, tenant_slug)

    def ai_key_check(self, user: Principal) -> None:
        self.spend(AI_KEY_CHECKS_PER_USER, user.user_id)


class MemoryUsageCounter:
    """Contador en memoria para un solo proceso (la API local y las pruebas). Solo guarda la ventana actual de cada contador."""

    def __init__(self) -> None:
        self._windows: dict[str, tuple[datetime, int]] = {}
        self._lock = threading.Lock()

    def hit(self, bucket: str, window_start: datetime) -> int:
        with self._lock:
            start, total = self._windows.get(bucket, (window_start, 0))
            total = total + 1 if start == window_start else 1
            self._windows[bucket] = (window_start, total)
            return total
