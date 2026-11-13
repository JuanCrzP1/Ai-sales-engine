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
# Migración 0016: el administrador y el asesor (ver `domain/business_config/team.py`).
MEMBER_ROLES = ("owner", "admin", "agent")
business_members = Table(
    "business_members",
    metadata,
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Text, primary_key=True),
    Column("role", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    # Migración 0011: el correo de la cuenta, tomado de su sesión, para los avisos por correo.
    Column("email", Text),
    CheckConstraint("role IN ('owner', 'admin', 'agent')", name="business_members_role_check"),
    Index("business_members_user_idx", "user_id"),
)

# Bandeja de conversaciones (ver `project/db/migrations/0004_conversations.sql`): el hilo de cada contacto en cada canal, de un
# solo negocio, y sus mensajes. Los datos de pago se guardan ocultos.
CONVERSATION_CHANNELS = ("whatsapp", "instagram", "telegram", "web", "api", "prueba")
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
    # Migración 0011: desde cuándo el cliente espera a una persona sin respuesta, y cuándo la IA retomó sola el chat.
    Column("customer_waiting_since", DateTime(timezone=True)),
    Column("ai_resumed_at", DateTime(timezone=True)),
    CheckConstraint("channel IN ('whatsapp', 'instagram', 'telegram', 'web', 'api', 'prueba')", name="conversations_channel_check"),
    CheckConstraint("stage IN ('new', 'interested', 'ready', 'payment', 'customer')", name="conversations_stage_check"),
    CheckConstraint("status IN ('open', 'closed')", name="conversations_status_check"),
    UniqueConstraint("tenant_id", "channel", "contact_ref", name="conversations_contact_key"),
    Index("conversations_tenant_recent_idx", "tenant_id", "last_message_at"),
    Index(
        "conversations_waiting_idx",
        "customer_waiting_since",
        postgresql_where=text("ai_paused AND customer_waiting_since IS NOT NULL"),
        sqlite_where=text("ai_paused AND customer_waiting_since IS NOT NULL"),
    ),
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
    CheckConstraint("kind IN ('handoff', 'ai_resumed')", name="notifications_kind_check"),
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

# Canales de cada negocio (migración 0008): WhatsApp por código QR con uazapi y, desde la 0018, Telegram con el bot del negocio. Los tokens van cifrados con la clave de los
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
    # Migración 0018: la cuenta del canal (en Telegram, el id y el usuario del bot). Un bot nunca queda en dos negocios.
    Column("account_id", Text),
    Column("account_username", Text),
    Index(
        "business_channels_account_key", "channel", "account_id", unique=True,
        postgresql_where=text("account_id IS NOT NULL"), sqlite_where=text("account_id IS NOT NULL"),
    ),
)

# Atención humana (migración 0011): el horario del equipo, lo que se le dice al cliente, cuándo retoma la IA y a qué correo llegan los
# avisos. Una fila por negocio; sin fila, los valores por defecto (`domain/business_config/attention.py`).
ATTENTION_HOURS_MODES = ("business", "custom", "always")
business_attention_settings = Table(
    "business_attention_settings",
    metadata,
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Column("hours_mode", Text, nullable=False, default="business"),
    Column("team_hours", JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=list),
    Column("timezone", Text, nullable=False, default="America/Bogota"),
    Column("reply_minutes", Integer, nullable=False, default=10),
    Column("resume_after_minutes", Integer),
    Column("email_enabled", Boolean, nullable=False, default=True),
    Column("email_to", Text),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_now),
    CheckConstraint("hours_mode IN ('business', 'custom', 'always')", name="business_attention_settings_hours_mode_check"),
    CheckConstraint(
        "reply_minutes BETWEEN 0 AND 1440 AND (resume_after_minutes IS NULL OR resume_after_minutes BETWEEN 1 AND 1440)",
        name="business_attention_settings_minutes_check",
    ),
)

# Cada aviso sale una sola vez por canal (correo, notificación push): la fila se reserva antes de enviar.
DELIVERY_CHANNELS = ("email", "push")
DELIVERY_STATUSES = ("sending", "sent", "failed", "skipped")
notification_deliveries = Table(
    "notification_deliveries",
    metadata,
    Column("notification_id", Uuid, ForeignKey("notifications.id", ondelete="CASCADE"), primary_key=True),
    Column("channel", Text, primary_key=True),
    Column("status", Text, nullable=False),
    Column("detail", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_now),
    CheckConstraint("channel IN ('email', 'push')", name="notification_deliveries_channel_check"),
    CheckConstraint("status IN ('sending', 'sent', 'failed', 'skipped')", name="notification_deliveries_status_check"),
)

# Los navegadores y celulares donde cada persona activó las notificaciones (Web Push).
push_subscriptions = Table(
    "push_subscriptions",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("user_id", Text, nullable=False),
    Column("endpoint", Text, nullable=False),
    Column("p256dh", Text, nullable=False),
    Column("auth", Text, nullable=False),
    Column("device", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Column("last_success_at", DateTime(timezone=True)),
    Index("push_subscriptions_endpoint_key", "endpoint", unique=True),
    Index("push_subscriptions_user_idx", "user_id"),
)

# Claves de la plataforma que se crean solas la primera vez (las de las notificaciones push). La parte secreta va cifrada con la
# clave de los datos de pago.
platform_keys = Table(
    "platform_keys",
    metadata,
    Column("name", Text, primary_key=True),
    Column("public_value", Text, nullable=False),
    Column("secret_ciphertext", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
)

# Claves de API de cada negocio (migración 0012): solo su huella y su comienzo visible; la clave completa se muestra una vez.
api_keys = Table(
    "api_keys",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    # El negocio de una clave de un solo negocio (`reach = 'one'`); vacío si entra a todos o a algunos (migración 0013).
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
    Column("name", Text, nullable=False),
    Column("prefix", Text, nullable=False),
    # La huella del valor de una clave; vacía en una conexión por OAuth, que no tiene valor fijo (migración 0014).
    Column("key_hash", Text, nullable=True),
    Column("scopes", JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=list),
    Column("created_by", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Column("last_used_at", DateTime(timezone=True)),
    Column("revoked_at", DateTime(timezone=True)),
    # La cuenta que la creó (Neon Auth); vacía en este equipo, sin cuentas.
    Column("owner_user_id", Text),
    Column("reach", Text, nullable=False, default="one", server_default="one"),
    Column("expires_at", DateTime(timezone=True)),
    # `key` (un valor fijo) u `oauth` (una conexión autorizada desde el agente, con el agente que la pidió).
    Column("kind", Text, nullable=False, default="key", server_default="key"),
    Column("client_id", Text),
    Index("api_keys_hash_key", "key_hash", unique=True),
    Index("api_keys_tenant_idx", "tenant_id", "created_at"),
    Index("api_keys_owner_idx", "owner_user_id", "created_at"),
    Index("api_keys_client_idx", "owner_user_id", "client_id"),
    CheckConstraint(
        "(reach = 'one' AND tenant_id IS NOT NULL) OR (reach IN ('all', 'some') AND tenant_id IS NULL)",
        name="api_keys_reach_check",
    ),
    CheckConstraint(
        "(kind = 'key' AND key_hash IS NOT NULL) OR (kind = 'oauth' AND key_hash IS NULL AND client_id IS NOT NULL)",
        name="api_keys_kind_check",
    ),
)

# Los negocios de una clave que entra a algunos (`reach = 'some'`).
api_key_businesses = Table(
    "api_key_businesses",
    metadata,
    Column("key_id", Uuid, ForeignKey("api_keys.id", ondelete="CASCADE"), primary_key=True),
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Index("api_key_businesses_tenant_idx", "tenant_id"),
)

# Los agentes que se registraron solos para conectarse por OAuth (migración 0014).
mcp_oauth_clients = Table(
    "mcp_oauth_clients",
    metadata,
    Column("client_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("redirect_uris", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
)

# Los códigos de autorización: su huella, un solo uso y 10 minutos.
mcp_oauth_codes = Table(
    "mcp_oauth_codes",
    metadata,
    Column("code_hash", Text, primary_key=True),
    Column("client_id", Text, ForeignKey("mcp_oauth_clients.client_id", ondelete="CASCADE"), nullable=False),
    Column("key_id", Uuid, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False),
    Column("redirect_uri", Text, nullable=False),
    Column("code_challenge", Text, nullable=False),
    Column("resource", Text),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Index("mcp_oauth_codes_expiry_idx", "expires_at"),
)

# Los tokens vigentes de cada conexión (sus huellas): de acceso (1 hora) y de renovación (30 días, cambia en cada uso).
mcp_oauth_tokens = Table(
    "mcp_oauth_tokens",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("key_id", Uuid, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False),
    Column("client_id", Text, ForeignKey("mcp_oauth_clients.client_id", ondelete="CASCADE"), nullable=False),
    Column("access_hash", Text, nullable=False),
    Column("access_expires_at", DateTime(timezone=True), nullable=False),
    Column("refresh_hash", Text, nullable=False),
    Column("refresh_expires_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Index("mcp_oauth_tokens_access_key", "access_hash", unique=True),
    Index("mcp_oauth_tokens_refresh_key", "refresh_hash", unique=True),
    Index("mcp_oauth_tokens_key_idx", "key_id"),
    Index("mcp_oauth_tokens_expiry_idx", "refresh_expires_at"),
)

# La respuesta a cada pedido con `Idempotency-Key` (migración 0012), cifrada, para devolver la misma si se repite (24 horas).
api_idempotency = Table(
    "api_idempotency",
    metadata,
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Column("idempotency_key", Text, primary_key=True),
    Column("response_ciphertext", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Index("api_idempotency_created_idx", "created_at"),
)

# Respuestas rápidas (migración 0015): los mensajes guardados de cada negocio que el equipo pone en un chat. El atajo es único en el
# negocio; los mensajes van en orden (`pieces`, una lista JSON de textos). Se borran con el negocio.
quick_replies = Table(
    "quick_replies",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    Column("shortcut", Text, nullable=False),
    Column("category", Text),
    Column("pieces", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("use_count", Integer, nullable=False, default=0),
    Column("last_used_at", DateTime(timezone=True)),
    Column("created_by", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_now),
    UniqueConstraint("tenant_id", "shortcut", name="quick_replies_shortcut_unique"),
    CheckConstraint("length(shortcut) BETWEEN 1 AND 40", name="quick_replies_shortcut_check"),
    CheckConstraint("category IS NULL OR length(category) BETWEEN 1 AND 40", name="quick_replies_category_check"),
    CheckConstraint("use_count >= 0", name="quick_replies_use_count_check"),
    Index("quick_replies_tenant_idx", "tenant_id", "category", "shortcut"),
)

# Las invitaciones al equipo de un negocio (ver `project/db/migrations/0016_team.sql`): solo la huella del enlace.
team_invitations = Table(
    "team_invitations",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    Column("email", Text, nullable=False),
    Column("role", Text, nullable=False),
    Column("token_hash", Text, nullable=False),
    Column("invited_by", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("accepted_at", DateTime(timezone=True)),
    Column("accepted_by", Text),
    Column("revoked_at", DateTime(timezone=True)),
    UniqueConstraint("token_hash", name="team_invitations_token_unique"),
    CheckConstraint("role IN ('owner', 'admin', 'agent')", name="team_invitations_role_check"),
    Index("team_invitations_tenant_idx", "tenant_id", "created_at"),
)

# Los archivos de las respuestas rápidas (ver `project/db/migrations/0017_quick_reply_files.sql`).
quick_reply_files = Table(
    "quick_reply_files",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid4),
    Column("tenant_id", Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    Column("mime_type", Text, nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("file_name", Text),
    Column("content", LargeBinary, nullable=False),
    Column("created_by", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_now),
    CheckConstraint("size_bytes BETWEEN 1 AND 4194304", name="quick_reply_files_size_check"),
    Index("quick_reply_files_tenant_idx", "tenant_id", "created_at"),
)
