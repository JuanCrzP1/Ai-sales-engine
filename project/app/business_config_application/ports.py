"""Lo que la aplicación necesita de la persistencia, sin depender de una base de datos.

`BusinessConfigStorage` y `PaymentSecretStorage` los implementan hoy `BusinessConfigRepository` y `PaymentSecretStore` sobre
SQLAlchemy, con SQLite en local. Pasar a PostgreSQL es cambiar la URL de conexión y aplicar la migración SQL, sin tocar a
quien usa estos puertos. Toda operación recibe el negocio y solo alcanza sus datos.
"""
from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any, Protocol, runtime_checkable

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
