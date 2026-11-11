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
    BigInteger,
    Boolean,
    LargeBinary,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    text,
    Numeric,
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
    # Migración 0005: el asistente la pasó a una persona y nadie la ha atendido todavía.
    Column("needs_human", Boolean, nullable=False, default=False),
    Column("handoff_requested_at", DateTime(timezone=True)),
    # Migración 0009: la bandeja en vivo. La IA pausada (la atiende una persona), por qué se pasó a una persona, los mensajes del
    # cliente sin leer, hasta cuándo el asistente está «escribiendo…» y cuándo cambió algo.
    Column("ai_paused", Boolean, nullable=False, default=False),
    Column("handoff_reason", Text),
    Column("unread_count", Integer, nullable=False, default=0),
    Column("assistant_typing_until", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_now),
    # Migración 0010: la etapa a la que llegó el cliente (solo avanza).
    Column("stage", Text, nullable=False, default="new"),
    CheckConstraint("channel IN ('whatsapp', 'instagram', 'telegram', 'web', 'prueba')", name="conversations_channel_check"),
    CheckConstraint("stage IN ('new', 'interested', 'ready', 'payment', 'customer')", name="conversations_stage_check"),
    CheckConstraint("status IN ('open', 'closed')", name="conversations_status_check"),
    UniqueConstraint("tenant_id", "channel", "contact_ref", name="conversations_contact_key"),
    Index("conversations_tenant_recent_idx", "tenant_id", "last_message_at"),
)

# Migración 0009: las fotos, audios y documentos de las conversaciones (el enlace de WhatsApp vence).
conversation_media = Table(
    "conversation_media",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    Column("conversation_id", Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
    Column("mime_type", Text, nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("file_name", Text),
    Column("content", LargeBinary, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Index("conversation_media_conversation_idx", "conversation_id"),
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
    # Migración 0009: el tipo, el estado, el id de WhatsApp, el archivo y lo que la IA entendió de él (transcripción o descripción).
    Column("kind", Text, nullable=False, default="text"),
    Column("status", Text, nullable=False, default="received"),
    Column("provider_message_id", Text),
    Column("media_id", Uuid, ForeignKey("conversation_media.id", ondelete="SET NULL")),
    Column("media_note", Text),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_now),
    CheckConstraint("author IN ('customer', 'assistant', 'agent')", name="conversation_entries_author_check"),
    CheckConstraint(
        "kind IN ('text', 'image', 'audio', 'video', 'document', 'sticker', 'location', 'contact', 'other')", name="conversation_entries_kind_check"
    ),
    CheckConstraint("status IN ('received', 'sending', 'sent', 'delivered', 'read', 'failed')", name="conversation_entries_status_check"),
    Index("conversation_entries_thread_idx", "conversation_id", "created_at"),
    Index(
        "conversation_entries_provider_key", "conversation_id", "provider_message_id", unique=True,
        postgresql_where=text("provider_message_id IS NOT NULL"), sqlite_where=text("provider_message_id IS NOT NULL"),
    ),
    Index("conversation_entries_live_idx", "conversation_id", "updated_at"),
    Index(
        "conversation_entries_provider_idx", "provider_message_id",
        postgresql_where=text("provider_message_id IS NOT NULL"), sqlite_where=text("provider_message_id IS NOT NULL"),
    ),
)

# Migración 0010: las ventas que registra el equipo. Anular una venta la deja marcada, no la borra.
sales = Table(
    "sales",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    Column("conversation_id", Uuid, ForeignKey("conversations.id", ondelete="SET NULL")),
    Column("customer_name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("amount", Numeric(14, 2), nullable=False),
    Column("currency", Text, nullable=False),
    Column("status", Text, nullable=False, default="confirmed"),
    Column("created_by", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Column("cancelled_at", DateTime(timezone=True)),
    CheckConstraint("status IN ('confirmed', 'cancelled')", name="sales_status_check"),
    Index("sales_tenant_recent_idx", "tenant_id", "created_at"),
)

# Avisos para el equipo de cada negocio (migración 0005). Cada persona marca como leídos los suyos en `notification_reads`.
notifications = Table(
    "notifications",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    Column("conversation_id", Uuid, ForeignKey("conversations.id", ondelete="CASCADE")),
    Column("kind", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("body", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    CheckConstraint("kind IN ('handoff')", name="notifications_kind_check"),
    Index("notifications_tenant_recent_idx", "tenant_id", "created_at"),
)

notification_reads = Table(
    "notification_reads",
    metadata,
    Column("notification_id", Uuid, ForeignKey("notifications.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Text, primary_key=True),
    Column("read_at", DateTime(timezone=True), nullable=False, default=_now),
)

# Contadores de los límites de uso (migración 0006): uno por qué se cuenta y de quién, y por ventana de tiempo.
rate_limits = Table(
    "rate_limits",
    metadata,
    Column("bucket", Text, primary_key=True),
    Column("window_start", DateTime(timezone=True), primary_key=True),
    Column("hits", Integer, nullable=False, default=0),
)

# Consumo de inteligencia artificial de cada negocio por día y modelo (migración 0007).
ai_usage = Table(
    "ai_usage",
    metadata,
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Column("day", Date, primary_key=True),
    Column("model", Text, primary_key=True),
    Column("replies", Integer, nullable=False, default=0),
    Column("prompt_tokens", BigInteger, nullable=False, default=0),
    Column("completion_tokens", BigInteger, nullable=False, default=0),
    Column("cost_usd", Numeric(14, 6, asdecimal=False)),
)

# Canales de cada negocio (migración 0008): por ahora WhatsApp por código QR con uazapi. Los tokens van cifrados con la clave de los
# datos de pago; `webhook_id` es el identificador secreto de la ruta del webhook del negocio.
business_channels = Table(
    "business_channels",
    metadata,
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Column("channel", Text, primary_key=True),
    Column("provider", Text, nullable=False),
    Column("server_url", Text, nullable=False),
    Column("token_ciphertext", Text, nullable=False),
    Column("webhook_id", Text, nullable=False, unique=True),
    Column("status", Text, nullable=False, default="disconnected"),
    Column("phone", Text),
    Column("profile_name", Text),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_now),
)
