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

# Tabla del esquema del motor (`project/docs/postgresql_schema.sql`): se declaran sus columnas obligatorias.
tenants = Table(
    "tenants",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", Text, nullable=False),
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

# Ajustes técnicos vigentes de cada negocio (`EngineSettings`): fuera del documento comercial y sin versiones.
business_engine_settings = Table(
    "business_engine_settings",
    metadata,
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Column("document", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_now),
)

# Inteligencia artificial de cada negocio: su modelo y su propia clave de OpenRouter, cifrada como los datos de pago. Fuera del
# contrato comercial; `key_hint` son los últimos caracteres de la clave, para reconocerla sin descifrarla.
business_ai_settings = Table(
    "business_ai_settings",
    metadata,
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Column("provider", Text, nullable=False),
    Column("model", Text),
    Column("key_ciphertext", Text),
    Column("key_hint", Text),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_now),
)

# Quién es miembro de cada negocio (ver `project/db/migrations/0003_business_members.sql`). `user_id` es el identificador del
# usuario en Neon Auth (`neon_auth.user`): cada persona solo llega a los negocios donde figura aquí.
MEMBER_ROLES = ("owner",)
business_members = Table(
    "business_members",
    metadata,
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Text, primary_key=True),
    Column("role", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    CheckConstraint("role IN ('owner')", name="business_members_role_check"),
    Index("business_members_user_idx", "user_id"),
)

# Bandeja de conversaciones (ver `project/db/migrations/0004_conversations.sql`): el hilo de cada contacto en cada canal, de un
# solo negocio, y sus mensajes. Los datos de pago se guardan ocultos.
CONVERSATION_CHANNELS = ("whatsapp", "instagram", "telegram", "web", "prueba")
conversations = Table(
    "conversations",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    Column("channel", Text, nullable=False),
    Column("contact_ref", Text, nullable=False),
    Column("contact_name", Text),
    Column("status", Text, nullable=False, default="open"),
    Column("started_at", DateTime(timezone=True), nullable=False, default=_now),
    Column("last_message_at", DateTime(timezone=True), nullable=False, default=_now),
    Column("last_message_preview", Text),
    Column("message_count", Integer, nullable=False, default=0),
    CheckConstraint("channel IN ('whatsapp', 'instagram', 'telegram', 'web', 'prueba')", name="conversations_channel_check"),
    CheckConstraint("status IN ('open', 'closed')", name="conversations_status_check"),
    UniqueConstraint("tenant_id", "channel", "contact_ref", name="conversations_contact_key"),
    Index("conversations_tenant_recent_idx", "tenant_id", "last_message_at"),
)

conversation_entries = Table(
    "conversation_entries",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("conversation_id", Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
    Column("author", Text, nullable=False),
    Column("body", Text, nullable=False),
    Column("intent", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    CheckConstraint("author IN ('customer', 'assistant', 'agent')", name="conversation_entries_author_check"),
    Index("conversation_entries_thread_idx", "conversation_id", "created_at"),
)
