"""Las migraciones del almacén en PostgreSQL (`project/db/migrations`): se aplican solas, nadie las corre a mano.

En la nube, la API del panel aplica al arrancar las que faltan (`ensure_migrations`), en orden, cada una en su transacción y con un
candado de PostgreSQL (`pg_advisory_xact_lock`), para que dos funciones que arrancan a la vez no choquen. Todas se pueden repetir
(`IF NOT EXISTS`), así que la segunda no cambia nada. Si algo falla, queda en el registro y el panel sigue con lo que ya había.
`scripts/setup_cloud_database.py` usa estas mismas funciones desde este equipo.

Una migración cuenta como aplicada cuando existen todas las tablas que crea; por eso cada migración crea al menos una tabla (una
prueba lo exige). En SQLite (este equipo) no hace nada: ahí las tablas salen de `tables.py`.
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
MIGRATIONS = sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql"))
# Un número fijo que identifica el candado de «migraciones del almacén».
LOCK_KEY = 8_150_204_118


def migration_tables(path: Path) -> set[str]:
    """Las tablas que crea una migración."""
    return set(re.findall(r"CREATE TABLE IF NOT EXISTS ([a-z_]+)", path.read_text(encoding="utf-8")))


def pending_migrations(engine: Engine) -> list[Path]:
    """Las migraciones a las que les falta alguna de sus tablas, en orden. No escribe nada."""
    tables = set(inspect(engine).get_table_names())
    return [path for path in MIGRATIONS if migration_tables(path) - tables]


def run_sql_file(engine: Engine, path: Path) -> None:
    """El archivo completo en una transacción, con el candado: si algo falla, no queda nada a medias."""
    sql = path.read_text(encoding="utf-8").replace("BEGIN;", "").replace("COMMIT;", "")
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.exec_driver_sql(f"BEGIN;\nSELECT pg_advisory_xact_lock({LOCK_KEY});\n{sql}\nCOMMIT;")


def apply_pending_migrations(engine: Engine) -> list[str]:
    """Aplica las migraciones que faltan y devuelve sus nombres. En una base que no es PostgreSQL no hace nada."""
    if engine.dialect.name != "postgresql":
        return []
    applied = []
    for path in pending_migrations(engine):
        run_sql_file(engine, path)
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
