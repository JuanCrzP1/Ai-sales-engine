"""Conexión del almacén de configuración de negocios.

La URL sale de `BUSINESS_CONFIG_DATABASE_URL`; sin ella se usa un archivo SQLite local. Esta base es
independiente de la del motor (`DATABASE_URL`). En PostgreSQL las tablas se crean con la migración
`project/db/migrations/0001_business_config_store.sql`, nunca desde aquí.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine, make_url

from app.business_config_application.assistant_lab import AssistantLabService
from app.business_config_application.ports import AIKeyVerifier, AssistantRunner
from app.business_config_application.service import BusinessConfigService
from app.business_config_application.conversations import PlaygroundRecorder
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.ai_settings_store import AISettingsStore
from app.infrastructure.business_config.ai_usage_store import AIUsageStore
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


def _with_psycopg(url: str) -> str:
    """Neon y Vercel entregan `postgres://` o `postgresql://`, que SQLAlchemy asocia con psycopg2; el proyecto usa psycopg 3.
    Es la misma regla de `normalize_database_url` del motor, repetida aquí porque este almacén no depende del motor."""
    for scheme in ("postgresql://", "postgres://"):
        if url.lower().startswith(scheme):
            return f"postgresql+psycopg://{url[len(scheme):]}"
    return url


def database_url() -> str:
    """La URL del almacén: la de `BUSINESS_CONFIG_DATABASE_URL` o, si no hay, el archivo SQLite local. Panel y motor usan esta."""
    return _with_psycopg(str(os.getenv(DATABASE_URL_ENV) or "").strip()) or f"sqlite:///{DEFAULT_LOCAL_DATABASE.as_posix()}"


def sqlite_file(url: str) -> Path | None:
    """El archivo de una URL de SQLite; None si la base no es un archivo SQLite."""
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite" or not parsed.database or parsed.database == ":memory:":
        return None
    return Path(parsed.database)


def create_business_config_engine(url: str | None = None) -> Engine:
    url = url or database_url()
    parsed = make_url(url)
    # Sin parámetros en los errores ni en los registros: incluyen documentos y datos de pago cifrados.
    if parsed.get_backend_name() != "sqlite":
        return create_engine(url, hide_parameters=True)
    if parsed.database and parsed.database != ":memory:":
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, hide_parameters=True)
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


# Columnas que una migración agregó a una tabla que ya existía: una base local anterior las recibe al arrancar el panel.
_ADDED_COLUMNS = {
    "conversations": {"needs_human": "BOOLEAN NOT NULL DEFAULT 0", "handoff_requested_at": "DATETIME"},
}


def create_local_schema(engine: Engine) -> None:
    """Crea las tablas en una base SQLite local y agrega las columnas nuevas a las que ya existían. En PostgreSQL se usa la
    migración SQL revisada."""
    if engine.dialect.name != "sqlite":
        raise ValueError("el esquema solo se crea desde aquí en SQLite: en PostgreSQL se aplica la migración SQL")
    metadata.create_all(engine)
    with engine.begin() as conn:
        for table, columns in _ADDED_COLUMNS.items():
            present = {column["name"] for column in inspect(conn).get_columns(table)}
            for name, definition in columns.items():
                if name not in present:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def build_business_config_service(engine: Engine, *, secrets_key: str | None = None) -> BusinessConfigService:
    """El servicio con la persistencia real. El repositorio comparte el almacén para guardar versión y datos de pago juntos."""
    secrets = PaymentSecretStore(engine, secrets_key)
    return BusinessConfigService(BusinessConfigRepository(engine, secrets), secrets)


def build_assistant_lab_service(
    engine: Engine,
    configs: BusinessConfigService,
    *,
    secrets_key: str | None = None,
    verifier: AIKeyVerifier | None = None,
    runner: AssistantRunner | None = None,
) -> AssistantLabService:
    """La inteligencia artificial y el área de pruebas, con la clave de IA de cada negocio cifrada en la misma base.

    Sin `runner` ni `verifier` (por ejemplo, en pruebas), guardar la configuración funciona y conversar responde que no está
    disponible: el motor se conecta en el arranque de la API (`scripts/run_admin_api.py`)."""
    recorder = PlaygroundRecorder(ConversationStore(engine))
    return AssistantLabService(
        configs, AISettingsStore(engine, secrets_key), verifier=verifier, runner=runner, recorder=recorder, usage=AIUsageStore(engine)
    )
