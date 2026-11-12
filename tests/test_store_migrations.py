"""Las migraciones del almacén se aplican solas en la nube, como en Auream: nadie las corre a mano.

- Cada una queda anotada en `schema_migrations`: se aplica una sola vez, aunque solo agregue columnas.
- Todas se pueden repetir: cada tabla, índice y columna lleva `IF NOT EXISTS`, y cada restricción se quita antes de crearla.
- En SQLite (este equipo) no hacen nada: ahí las tablas salen de `tables.py`.
- Si aplicarlas falla al arrancar, se registra y la API sigue con lo que ya había.
- La API del panel en la nube las aplica al arrancar.

La prueba contra PostgreSQL real (todas, otra vez sin cambios, una nueva que solo agrega columnas y cuatro arranques a la vez) se hizo
contra el PostgreSQL de este equipo, en un esquema temporal.
"""
from __future__ import annotations

import inspect as source
import re

from sqlalchemy import create_engine

from app import cloud_panel
from app.infrastructure.business_config import migrations


def test_migrations_are_ordered_and_every_statement_can_run_again():
    names = [path.name for path in migrations.MIGRATIONS]
    assert names == sorted(names) and names[-1] == "0011_human_attention.sql"
    assert all(migrations.MIGRATION_NAME.fullmatch(name) for name in names)
    for path in migrations.MIGRATIONS:
        sql = re.sub(r"--[^\n]*", "", path.read_text(encoding="utf-8"))
        for statement in re.findall(r"CREATE (?:UNIQUE )?(?:TABLE|INDEX)[^;]*|ADD COLUMN[^;]*", sql):
            assert "IF NOT EXISTS" in statement, (path.name, statement[:80])
        for constraint in re.findall(r"ADD CONSTRAINT (\w+)", sql):
            assert f"DROP CONSTRAINT IF EXISTS {constraint}" in sql, (path.name, constraint)


def test_the_tracking_table_is_written_in_the_same_transaction(monkeypatch):
    executed = []

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def execution_options(self, **_):
            return self

        def exec_driver_sql(self, sql):
            executed.append(sql)

    class Engine:
        def connect(self):
            return Connection()

    migrations.run_sql_file(Engine(), migrations.MIGRATIONS_DIR / "0009_conversations_live.sql", record=True)
    (sql,) = executed
    assert sql.startswith("BEGIN;") and sql.rstrip().endswith("COMMIT;")
    assert sql.index("pg_advisory_xact_lock") < sql.index("conversation_media") < sql.index("INSERT INTO schema_migrations")
    assert "VALUES ('0009_conversations_live.sql') ON CONFLICT (name) DO NOTHING" in sql


def test_on_sqlite_nothing_is_applied():
    assert migrations.apply_pending_migrations(create_engine("sqlite://")) == []


def test_a_failure_at_startup_is_logged_and_does_not_stop_the_api(monkeypatch):
    logged = []
    monkeypatch.setattr(migrations, "apply_pending_migrations", lambda _engine: (_ for _ in ()).throw(RuntimeError("sin conexión")))
    monkeypatch.setattr(migrations.logger, "error", lambda event, **kwargs: logged.append((event, kwargs["extra"])))
    migrations.ensure_migrations(create_engine("sqlite://"))
    assert logged == [("migraciones_fallaron", {"error": "RuntimeError"})]


def test_the_cloud_panel_applies_them_when_it_starts():
    body = source.getsource(cloud_panel.build_cloud_panel_api)
    assert body.index("ensure_migrations(engine)") < body.index("build_business_config_service(")
