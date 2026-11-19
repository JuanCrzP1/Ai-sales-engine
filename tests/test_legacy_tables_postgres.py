"""Las tablas del sistema anterior se retiran (`0023_retire_legacy_tables.sql`), contra un PostgreSQL de verdad (`TEST_POSTGRES_URL`).

Cada prueba trabaja en su propio esquema temporal, con las tablas como estaban en producción antes de retirarlas: la migración
borra las cuatro y deja intactos los negocios y la memoria del motor, se puede aplicar otra vez, y si algo inesperado dependiera
de una de ellas falla sin borrar nada. El esquema del motor (`postgresql_schema.sql`) ya no las crea.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.infrastructure.business_config.migrations import MIGRATIONS_DIR, run_sql_file

URL = os.getenv("TEST_POSTGRES_URL", "").strip()
pytestmark = pytest.mark.skipif(not URL, reason="requiere TEST_POSTGRES_URL (una base PostgreSQL vacía para pruebas)")
SCHEMA = Path(__file__).resolve().parents[1] / "project" / "docs" / "postgresql_schema.sql"
MIGRATION = MIGRATIONS_DIR / "0023_retire_legacy_tables.sql"
LEGACY = ("admin_users", "tenant_secrets", "tenant_channels", "tenant_settings")
# Como estaban en `postgresql_schema.sql` (y en Neon) antes del 18 de noviembre de 2026.
LEGACY_DDL = """
CREATE TABLE admin_users (id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  email TEXT UNIQUE, password_hash TEXT, name TEXT, phone TEXT, document_number TEXT, company_name TEXT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE tenant_secrets (tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE, encrypted_data JSONB,
  created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE tenant_channels (id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  channel TEXT, config JSONB, is_active BOOLEAN DEFAULT true);
CREATE TABLE tenant_settings (tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE, settings JSONB);
"""


@pytest.fixture
def database():
    """Un esquema temporal con las tablas del motor, las cuatro del sistema anterior y un negocio con su memoria."""
    name = f"retiro_{uuid.uuid4().hex[:10]}"
    admin = create_engine(URL)
    with admin.begin() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.execute(text(f'CREATE SCHEMA "{name}"'))
    engine = create_engine(URL, connect_args={"options": f"-csearch_path={name},public"})
    with engine.begin() as conn:
        conn.exec_driver_sql(SCHEMA.read_text(encoding="utf-8").replace('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";', ""))
        conn.exec_driver_sql(LEGACY_DDL)
        tenant = conn.execute(text("INSERT INTO tenants (name, slug) VALUES ('Negocio', 'negocio') RETURNING id")).scalar()
        client = conn.execute(text("INSERT INTO clients (tenant_id, external_id) VALUES (:t, '573001112233') RETURNING id"), {"t": tenant}).scalar()
        conn.execute(text("INSERT INTO conversation_messages (tenant_id, client_id, role, content) VALUES (:t, :c, 'user', 'Hola')"), {"t": tenant, "c": client})
        conn.execute(text("INSERT INTO admin_users (tenant_id, name) VALUES (:t, 'negocio')"), {"t": tenant})
        conn.execute(text("INSERT INTO tenant_settings (tenant_id, settings) VALUES (:t, '{}')"), {"t": tenant})
    yield engine
    engine.dispose()
    with admin.begin() as conn:
        conn.execute(text(f'DROP SCHEMA "{name}" CASCADE'))
    admin.dispose()


def _tables(engine) -> set[str]:
    with engine.connect() as conn:
        return {row[0] for row in conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"))}


def test_the_four_tables_go_and_the_businesses_and_their_memory_stay(database):
    run_sql_file(database, MIGRATION, record=True)
    assert not set(LEGACY) & _tables(database)
    with database.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM tenants")).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM clients")).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM conversation_messages")).scalar() == 1
        assert conn.execute(text("SELECT name FROM schema_migrations")).scalars().all() == [MIGRATION.name]
    # Otra vez, como cuando una base recibe el registro de migraciones por primera vez: no cambia nada.
    run_sql_file(database, MIGRATION, record=True)
    assert not set(LEGACY) & _tables(database)


def test_if_something_depended_on_one_nothing_is_dropped(database):
    with database.begin() as conn:
        conn.execute(text("CREATE VIEW cuentas_viejas AS SELECT name FROM admin_users"))
    with pytest.raises(DBAPIError):
        run_sql_file(database, MIGRATION, record=True)
    assert set(LEGACY) <= _tables(database)
    assert "schema_migrations" not in _tables(database)


def test_the_engine_schema_no_longer_creates_them():
    sql = SCHEMA.read_text(encoding="utf-8")
    assert not [table for table in LEGACY if f"CREATE TABLE {table}" in sql]
