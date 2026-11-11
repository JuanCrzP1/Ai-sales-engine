"""Las migraciones del almacén se aplican solas en la nube, como en Auream: nadie las corre a mano.

- Cada migración crea al menos una tabla: así se sabe si falta (`pending_migrations`).
- En SQLite (este equipo) no hacen nada: ahí las tablas salen de `tables.py`.
- Si aplicarlas falla al arrancar, se registra y la API sigue con lo que ya había.
- La API del panel en la nube las aplica al arrancar.

La prueba contra PostgreSQL real (todas, otra vez sin cambios, la que falta y cuatro arranques a la vez) se hizo contra el
PostgreSQL de este equipo, en un esquema temporal.
"""
from __future__ import annotations

import inspect as source

from sqlalchemy import create_engine

from app import cloud_panel
from app.infrastructure.business_config import migrations
from app.infrastructure.business_config.tables import metadata


def test_every_migration_creates_at_least_one_known_table():
    assert [path.name for path in migrations.MIGRATIONS][-1] == "0008_business_channels.sql"
    for path in migrations.MIGRATIONS:
        tables = migrations.migration_tables(path)
        assert tables, f"{path.name} no crea ninguna tabla: no se podría saber si falta"
        assert tables <= set(metadata.tables), path.name
    assert migrations.migration_tables(migrations.MIGRATIONS_DIR / "0008_business_channels.sql") == {"business_channels"}


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
