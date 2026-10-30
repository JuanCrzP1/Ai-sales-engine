"""Tablas del almacén de configuración de negocios (ver `project/db/migrations/0001_business_config_store.sql`).

Son la misma definición que la migración SQL, expresada para SQLAlchemy y portable a SQLite en las
pruebas. En PostgreSQL (Neon) las tablas se crean con la migración revisada, nunca desde aquí.

Los negocios se identifican por UUID (`tenants.id`), como en `project/docs/postgresql_schema.sql` y
en la ruta conversacional. Los modelos ORM con ids enteros (`app/models`) no se usan aquí.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

CONFIG_STATUSES = ("draft", "published", "archived")


def _now() -> datetime:
    return datetime.now(timezone.utc)


metadata = MetaData()

# Tabla existente del esquema del motor: se declara solo para la clave foránea y para resolver el slug.
tenants = Table(
    "tenants",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("slug", Text, nullable=False, unique=True),
)

business_configs = Table(
    "business_configs",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    Column("version", Integer, nullable=False),
    Column("schema_version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("document", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("content_hash", Text, nullable=False),
    Column("created_by", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Column("published_at", DateTime(timezone=True)),
    UniqueConstraint("tenant_id", "version"),
    CheckConstraint("version > 0", name="business_configs_version_positive"),
    CheckConstraint(f"status IN {CONFIG_STATUSES}", name="business_configs_status"),
)

# Como máximo una versión publicada por negocio.
Index(
    "business_configs_one_published",
    business_configs.c.tenant_id,
    unique=True,
    postgresql_where=business_configs.c.status == "published",
    sqlite_where=business_configs.c.status == "published",
)

# Datos de pago referenciados como {"secret_ref": "secret_store:<ref_key>"}; solo texto cifrado.
business_config_secrets = Table(
    "business_config_secrets",
    metadata,
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Column("ref_key", Text, primary_key=True),
    Column("ciphertext", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_now),
)
