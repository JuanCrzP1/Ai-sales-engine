-- ============================================================================
-- 0004_conversations.sql
--
-- Bandeja de conversaciones del panel. `conversations` es el hilo de un contacto
-- en un canal (un número de WhatsApp, un chat de Telegram...) y pertenece a un solo
-- negocio; `conversation_entries` son sus mensajes. Las del área de pruebas usan el
-- canal 'prueba'. Los datos de pago se guardan ocultos ("[dato de pago]").
-- No reemplaza las tablas del motor (`clients`, `conversation_messages`,
-- `conversation_memory`): es lo que muestra el panel.
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py; una prueba comprueba que
-- ambas coinciden. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS conversations (
  id                    UUID PRIMARY KEY,
  tenant_id             UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  channel               TEXT NOT NULL,
  contact_ref           TEXT NOT NULL,
  contact_name          TEXT,
  status                TEXT NOT NULL DEFAULT 'open',
  started_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_message_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_message_preview  TEXT,
  message_count         INTEGER NOT NULL DEFAULT 0,
  CONSTRAINT conversations_channel_check CHECK (channel IN ('whatsapp', 'instagram', 'telegram', 'web', 'prueba')),
  CONSTRAINT conversations_status_check CHECK (status IN ('open', 'closed')),
  CONSTRAINT conversations_contact_key UNIQUE (tenant_id, channel, contact_ref)
);

CREATE INDEX IF NOT EXISTS conversations_tenant_recent_idx ON conversations (tenant_id, last_message_at);

CREATE TABLE IF NOT EXISTS conversation_entries (
  id               UUID PRIMARY KEY,
  conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  author           TEXT NOT NULL,
  body             TEXT NOT NULL,
  intent           TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT conversation_entries_author_check CHECK (author IN ('customer', 'assistant', 'agent'))
);

CREATE INDEX IF NOT EXISTS conversation_entries_thread_idx ON conversation_entries (conversation_id, created_at);

COMMIT;
