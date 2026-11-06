"""Conexión del almacén de configuración de negocios.

La URL sale de `BUSINESS_CONFIG_DATABASE_URL`; sin ella se usa un archivo SQLite local. Esta base es
independiente de la del motor (`DATABASE_URL`). En PostgreSQL las tablas se crean con la migración
`project/db/migrations/0001_business_config_store.sql`, nunca desde aquí.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url

from app.business_config_application.service import BusinessConfigService
from app.infrastructure.business_config.payment_secret_store import PaymentSecretStore
from app.infrastructure.business_config.repository import BusinessConfigRepository
from app.infrastructure.business_config.tables import metadata

DATABASE_URL_ENV = "BUSINESS_CONFIG_DATABASE_URL"
DEFAULT_LOCAL_DATABASE = Path(__file__).resolve().parents[3] / "data" / "business_config.sqlite3"


def _enable_foreign_keys(connection, _record) -> None:
    # SQLite no aplica claves foráneas salvo que se active en cada conexión.
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_business_config_engine(url: str | None = None) -> Engine:
    url = url or os.getenv(DATABASE_URL_ENV) or f"sqlite:///{DEFAULT_LOCAL_DATABASE.as_posix()}"
    parsed = make_url(url)
    # Sin parámetros en los errores ni en los registros: incluyen documentos y datos de pago cifrados.
    if parsed.get_backend_name() != "sqlite":
        return create_engine(url, hide_parameters=True)
    if parsed.database and parsed.database != ":memory:":
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, hide_parameters=True)
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def create_local_schema(engine: Engine) -> None:
    """Crea las tablas en una base SQLite local. En PostgreSQL se usa la migración SQL revisada."""
    if engine.dialect.name != "sqlite":
        raise ValueError("el esquema solo se crea desde aquí en SQLite: en PostgreSQL se aplica la migración SQL")
    metadata.create_all(engine)


def build_business_config_service(engine: Engine, *, secrets_key: str | None = None) -> BusinessConfigService:
    """El servicio con la persistencia real. El repositorio comparte el almacén para guardar versión y datos de pago juntos."""
    secrets = PaymentSecretStore(engine, secrets_key)
    return BusinessConfigService(BusinessConfigRepository(engine, secrets), secrets)
