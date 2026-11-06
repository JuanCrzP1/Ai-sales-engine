"""Lo que se guarda y se consulta de cada negocio, sin depender de cómo se almacena."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.domain.business_config.contract import BusinessConfig

PaymentFieldStatus = Literal["configured", "missing", "unreadable"]


@dataclass(frozen=True)
class ConfigVersion:
    version: int
    status: str
    content_hash: str
    published_at: datetime | None
    created_at: datetime | None = None
    created_by: str | None = None


@dataclass(frozen=True)
class StoredConfig:
    """Una versión guardada con su contenido, ya validado."""

    version: ConfigVersion
    config: BusinessConfig


@dataclass(frozen=True)
class BusinessSummary:
    slug: str
    name: str
    latest_version: int | None
    draft_version: int | None
    published_version: int | None


@dataclass(frozen=True)
class PaymentFieldState:
    """Lo que se informa de un dato de pago: si se puede usar y, solo entonces, una versión enmascarada para reconocerlo."""

    status: PaymentFieldStatus
    masked: str | None = None
