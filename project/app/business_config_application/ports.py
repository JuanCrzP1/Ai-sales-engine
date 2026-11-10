"""Lo que la aplicación necesita de la persistencia, sin depender de una base de datos.

`BusinessConfigStorage` y `PaymentSecretStorage` los implementan hoy `BusinessConfigRepository` y `PaymentSecretStore` sobre
SQLAlchemy, con SQLite en local. Pasar a PostgreSQL es cambiar la URL de conexión y aplicar la migración SQL, sin tocar a
quien usa estos puertos. Toda operación recibe el negocio y solo alcanza sus datos.
"""
from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from app.domain.business_config.ai_settings import AICredentials, AISettings, AssistantTurn, KeyCheck
from app.domain.business_config.contract import BusinessConfig, SecretRef
from app.domain.business_config.records import BusinessSummary, ConfigVersion, StoredConfig


class _VersionCheck(Enum):
    ANY = "any"


ANY_VERSION = _VersionCheck.ANY
# La versión más reciente que conocía quien guarda (None: ninguna). `ANY_VERSION` guarda sin comprobarlo.
ExpectedVersion = int | None | _VersionCheck
PublishCheck = Callable[[BusinessConfig], None]


@runtime_checkable
class BusinessConfigStorage(Protocol):
    def create_business(self, tenant_slug: str, name: str) -> BusinessSummary: ...

    def business(self, tenant_slug: str) -> BusinessSummary: ...

    def list_businesses(self) -> list[BusinessSummary]: ...

    def delete_business(self, tenant_slug: str) -> None: ...

    def save_draft(
        self,
        tenant_slug: str,
        document: dict[str, Any],
        *,
        created_by: str | None = None,
        expected_version: ExpectedVersion = ANY_VERSION,
        payment_secrets: dict[str, str] | None = None,
    ) -> ConfigVersion:
        """Guarda una versión y sus datos de pago de forma atómica: o queda todo o no queda nada."""
        ...

    def latest_draft(self, tenant_slug: str) -> StoredConfig | None: ...

    def version(self, tenant_slug: str, version: int) -> StoredConfig: ...

    def published(self, tenant_slug: str) -> BusinessConfig: ...

    def publish(self, tenant_slug: str, version: int, *, check: PublishCheck | None = None) -> None: ...

    def rollback(self, tenant_slug: str, *, check: PublishCheck | None = None) -> int: ...

    def history(self, tenant_slug: str) -> list[ConfigVersion]: ...

    def save_engine_settings(self, tenant_slug: str, document: dict[str, Any]) -> None: ...


@runtime_checkable
class PaymentSecretStorage(Protocol):
    def resolver(self, tenant_slug: str) -> Callable[[SecretRef], str]: ...

    def known_values(self, tenant_slug: str) -> list[str]: ...

    def verify_key(self) -> None: ...


@runtime_checkable
class AISettingsStorage(Protocol):
    """La inteligencia artificial de cada negocio, con su clave cifrada. Cada negocio solo alcanza la suya."""

    def ai_settings(self, tenant_slug: str) -> AISettings: ...

    def ai_credentials(self, tenant_slug: str) -> AICredentials | None: ...

    def save_ai_settings(self, tenant_slug: str, *, model: str | None, api_key: str | None, clear_key: bool) -> AISettings: ...


@runtime_checkable
class AIKeyVerifier(Protocol):
    """Pregunta al proveedor si la clave es válida, sin gastar créditos."""

    def verify(self, credentials: AICredentials) -> KeyCheck: ...


@runtime_checkable
class AssistantRunner(Protocol):
    """El motor respondiendo con una configuración concreta, en una conversación de prueba aislada de los clientes reales.

    `sections` es lo compilado de esa versión: puede llevar datos de pago descifrados y no se guarda ni se registra.
    """

    def reply(self, *, tenant_slug: str, sections: dict[str, dict], credentials: AICredentials, session_id: str, message: str) -> AssistantTurn: ...

    def reset(self, *, tenant_slug: str, session_id: str) -> None: ...
