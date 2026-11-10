"""Acceso de solo lectura del motor a lo publicado en el almacén de BusinessConfig.

El motor lee la misma base que escribe el panel (`database_url()`: `BUSINESS_CONFIG_DATABASE_URL` o el SQLite local) con la misma
clave de cifrado (`find_secrets_key()`). Nunca crea la base, las tablas ni la clave, y nunca escribe: si algo falta, lo informa con una
excepción y el llamador decide (el cargador del motor vuelve a los YAML).

Es la única puerta del motor hacia este almacén: el motor no conoce tablas, conexiones ni cifrado.
"""
from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.engine import Engine

from app.domain.business_config.contract import BusinessConfig, SecretRef
from app.domain.business_config.errors import BusinessConfigError
from app.infrastructure.business_config.database import create_business_config_engine, database_url, sqlite_file
from app.infrastructure.business_config.payment_secret_store import SECRET_STORE_SOURCE, PaymentSecretStore
from app.infrastructure.business_config.repository import BusinessConfigRepository
from app.infrastructure.business_config.secrets_key import find_secrets_key

__all__ = ["SECRET_STORE_SOURCE", "PublishedConfigReader", "dispose_shared_engines", "open_published_reader", "reader_for"]


@dataclass(frozen=True)
class PublishedConfigReader:
    """Lo publicado de cada negocio y el resolutor de sus datos de pago cifrados."""

    _repository: BusinessConfigRepository
    _secrets: PaymentSecretStore

    def published(self, tenant_slug: str) -> BusinessConfig:
        return self._repository.published(tenant_slug)

    def payment_resolver(self, tenant_slug: str) -> Callable[[SecretRef], str]:
        return self._secrets.resolver(tenant_slug)


def reader_for(engine: Engine, key: str | None = None) -> PublishedConfigReader:
    """Un lector sobre una conexión ya abierta. Sin `key`, la clave sale de `BUSINESS_CONFIG_SECRETS_KEY`."""
    secrets = PaymentSecretStore(engine, key)
    return PublishedConfigReader(BusinessConfigRepository(engine, secrets), secrets)


# Una conexión por URL para todo el proceso: el motor consulta el almacén en cada mensaje.
_engines: dict[str, Engine] = {}
_engines_lock = threading.Lock()


def _shared_engine(url: str) -> Engine:
    with _engines_lock:
        if url not in _engines:
            _engines[url] = create_business_config_engine(url)
        return _engines[url]


def open_published_reader() -> PublishedConfigReader:
    """El lector del almacén que usa el panel en este equipo, o en la nube cuando `BUSINESS_CONFIG_DATABASE_URL` apunte allí."""
    url = database_url()
    path = sqlite_file(url)
    if path is not None and not path.is_file():
        # Sin esta comprobación, SQLite crearía un archivo vacío: el motor nunca debe crear el almacén.
        raise BusinessConfigError("no existe el almacén de BusinessConfig: se crea con scripts/init_local_business_config.py")
    return reader_for(_shared_engine(url), find_secrets_key())


def dispose_shared_engines() -> None:
    """Cierra las conexiones compartidas (al terminar el proceso o entre pruebas)."""
    with _engines_lock:
        for engine in _engines.values():
            engine.dispose()
        _engines.clear()
