"""Las migraciones del almacén en PostgreSQL (`project/db/migrations`): se aplican solas, nadie las corre a mano.

En la nube, la API del panel aplica al arrancar las que faltan (`ensure_migrations`), en orden, cada una en su transacción y con un
candado de PostgreSQL (`pg_advisory_xact_lock`), para que dos funciones que arrancan a la vez no choquen. Cada una queda anotada en
`schema_migrations` en la misma transacción: se aplica una sola vez, aunque solo agregue columnas. Todas se pueden repetir
(`IF NOT EXISTS`), así que la primera vez que una base tiene el registro, las anteriores se vuelven a pasar sin cambiar nada. Si algo
falla, queda en el registro y el panel sigue con lo que ya había. `scripts/setup_cloud_database.py` usa estas mismas funciones.

En SQLite (este equipo) no hace nada: ahí las tablas salen de `tables.py` (`create_local_schema`).
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

# El mismo registro del motor (`app.utils.logger`), sin depender de él: esta capa solo usa la biblioteca estándar y SQLAlchemy.
logger = logging.getLogger("assistant")

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "db" / "migrations"
MIGRATION_NAME = re.compile(r"[0-9]{4}_[a-z0-9_]+\.sql")
MIGRATIONS = sorted(path for path in MIGRATIONS_DIR.glob("*.sql") if MIGRATION_NAME.fullmatch(path.name))
TRACKING_TABLE = "schema_migrations"
# Un número fijo que identifica el candado de «migraciones del almacén».
LOCK_KEY = 8_150_204_118

_TRACKING_DDL = f"""
CREATE TABLE IF NOT EXISTS {TRACKING_TABLE} (
  name        TEXT PRIMARY KEY,
  applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);"""


def applied_migrations(engine: Engine) -> set[str]:
    """Los nombres de las migraciones ya aplicadas en esa base. Sin registro todavía, ninguna."""
    if not inspect(engine).has_table(TRACKING_TABLE):
        return set()
    with engine.connect() as connection:
        return {row[0] for row in connection.exec_driver_sql(f"SELECT name FROM {TRACKING_TABLE}")}


def pending_migrations(engine: Engine) -> list[Path]:
    """Las migraciones que esa base no tiene anotadas, en orden. No escribe nada."""
    applied = applied_migrations(engine)
    return [path for path in MIGRATIONS if path.name not in applied]


def run_sql_file(engine: Engine, path: Path, *, record: bool = False) -> None:
    """El archivo completo en una transacción, con el candado: si algo falla, no queda nada a medias. Con `record`, lo anota."""
    sql = path.read_text(encoding="utf-8").replace("BEGIN;", "").replace("COMMIT;", "")
    track = ""
    if record:
        if not MIGRATION_NAME.fullmatch(path.name):
            raise ValueError(f"nombre de migración no válido: {path.name}")
        track = f"{_TRACKING_DDL}\nINSERT INTO {TRACKING_TABLE} (name) VALUES ('{path.name}') ON CONFLICT (name) DO NOTHING;"
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.exec_driver_sql(f"BEGIN;\nSELECT pg_advisory_xact_lock({LOCK_KEY});\n{sql}\n{track}\nCOMMIT;")


def apply_pending_migrations(engine: Engine) -> list[str]:
    """Aplica y anota las migraciones que faltan, y devuelve sus nombres. En una base que no es PostgreSQL no hace nada."""
    if engine.dialect.name != "postgresql":
        return []
    applied = []
    for path in pending_migrations(engine):
        run_sql_file(engine, path, record=True)
        applied.append(path.name)
    return applied


def ensure_migrations(engine: Engine) -> None:
    """Al arrancar en la nube: deja la base al día. Un fallo no tumba la API (lo que ya había sigue sirviendo), pero se registra."""
    try:
        applied = apply_pending_migrations(engine)
    except Exception as exc:  # noqa: BLE001 - se registra y la API sigue con el esquema que ya tenía
        logger.error("migraciones_fallaron", extra={"error": type(exc).__name__})
        return
    if applied:
        logger.info("migraciones_aplicadas", extra={"migraciones": applied})
