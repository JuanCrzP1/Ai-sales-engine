-- ============================================================================
-- 0009_conversations_live.sql
--
-- La bandeja en vivo, como una empresa de atención:
--   · cada mensaje guarda su tipo (texto, foto, audio, video, documento,
--     sticker, ubicación…), su estado (recibido; enviando, enviado, entregado,
--     leído o fallido) y el id que le dio WhatsApp: el mismo aviso repetido no
--     se guarda dos veces (índice único por conversación) y los recibos de
--     entregado y leído encuentran su mensaje
--   · las fotos, audios y documentos se guardan aquí (`conversation_media`),
--     porque el enlace de WhatsApp vence; el audio y la foto llevan lo que la IA
--     entendió de ellos (`media_note`: la transcripción o la descripción)
--   · cada conversación sabe si la IA está pausada (la atiende una persona),
--     por qué se pasó a una persona, cuántos mensajes del cliente nadie ha leído
--     y hasta cuándo el asistente está «escribiendo…»
--   · `updated_at`: el panel pide solo lo nuevo o lo que cambió desde la última
--     vez, en lugar del hilo completo cada pocos segundos
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py. Se puede aplicar más de
-- una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS conversation_media (
  id               UUID PRIMARY KEY,
  tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  mime_type        TEXT NOT NULL,
  size_bytes       INTEGER NOT NULL,
  file_name        TEXT,
  content          BYTEA NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS ai_paused BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS handoff_reason TEXT;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS unread_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS assistant_typing_until TIMESTAMPTZ;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE conversation_entries ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT 'text';
ALTER TABLE conversation_entries ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'received';
ALTER TABLE conversation_entries ADD COLUMN IF NOT EXISTS provider_message_id TEXT;
ALTER TABLE conversation_entries ADD COLUMN IF NOT EXISTS media_id UUID REFERENCES conversation_media(id) ON DELETE SET NULL;
ALTER TABLE conversation_entries ADD COLUMN IF NOT EXISTS media_note TEXT;
ALTER TABLE conversation_entries ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Lo que el asistente y el equipo ya habían enviado antes de esta migración, salió.
UPDATE conversation_entries SET status = 'sent' WHERE author <> 'customer' AND status = 'received';

ALTER TABLE conversation_entries DROP CONSTRAINT IF EXISTS conversation_entries_kind_check;
ALTER TABLE conversation_entries ADD CONSTRAINT conversation_entries_kind_check
  CHECK (kind IN ('text', 'image', 'audio', 'video', 'document', 'sticker', 'location', 'contact', 'other'));
ALTER TABLE conversation_entries DROP CONSTRAINT IF EXISTS conversation_entries_status_check;
ALTER TABLE conversation_entries ADD CONSTRAINT conversation_entries_status_check
  CHECK (status IN ('received', 'sending', 'sent', 'delivered', 'read', 'failed'));

-- El mismo mensaje de WhatsApp, una sola vez por conversación (los avisos pueden repetirse).
CREATE UNIQUE INDEX IF NOT EXISTS conversation_entries_provider_key
  ON conversation_entries (conversation_id, provider_message_id) WHERE provider_message_id IS NOT NULL;
-- «Lo que cambió desde…» de un chat.
CREATE INDEX IF NOT EXISTS conversation_entries_live_idx ON conversation_entries (conversation_id, updated_at);
-- Los recibos de entregado y leído buscan por el id de WhatsApp de lo que salió.
CREATE INDEX IF NOT EXISTS conversation_entries_provider_idx
  ON conversation_entries (provider_message_id) WHERE provider_message_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS conversation_media_conversation_idx ON conversation_media (conversation_id);

COMMIT;
