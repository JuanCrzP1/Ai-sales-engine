-- ============================================================================
-- 0011_human_attention.sql
--
-- Atención humana completa:
--   · `business_attention_settings`: el horario del equipo (el del negocio,
--     uno propio o siempre), su zona horaria, cuánto le decimos al cliente que
--     tarda el equipo, cuándo retoma la IA un chat que nadie atendió y a qué
--     correo llegan los avisos. Son ajustes de la operación: no tienen versiones.
--   · `business_members.email`: el correo de la cuenta del dueño, tomado de su
--     sesión, para avisarle por correo sin leer las tablas internas de Neon Auth.
--   · `conversations.customer_waiting_since`: desde cuándo el cliente espera a
--     una persona sin respuesta (la IA está pausada). Lo borra la respuesta del
--     equipo o la IA al retomar. `ai_resumed_at`: cuándo la retomó la IA sola.
--   · avisos `ai_resumed` (la IA retomó un chat que nadie atendió).
--   · `notification_deliveries`: cada aviso sale una sola vez por correo y una
--     por notificación push, aunque dos procesos lo intenten a la vez.
--   · `push_subscriptions`: los navegadores y celulares donde cada persona
--     activó las notificaciones.
--   · `platform_keys`: las claves de la plataforma que se crean solas (las de
--     las notificaciones push), con la parte secreta cifrada.
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py. Se puede aplicar más de
-- una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS business_attention_settings (
  tenant_id             UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  hours_mode            TEXT NOT NULL DEFAULT 'business',
  team_hours            JSONB NOT NULL DEFAULT '[]'::jsonb,
  timezone              TEXT NOT NULL DEFAULT 'America/Bogota',
  reply_minutes         INTEGER NOT NULL DEFAULT 10,
  resume_after_minutes  INTEGER,
  email_enabled         BOOLEAN NOT NULL DEFAULT true,
  email_to              TEXT,
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE business_attention_settings DROP CONSTRAINT IF EXISTS business_attention_settings_hours_mode_check;
ALTER TABLE business_attention_settings ADD CONSTRAINT business_attention_settings_hours_mode_check
  CHECK (hours_mode IN ('business', 'custom', 'always'));
ALTER TABLE business_attention_settings DROP CONSTRAINT IF EXISTS business_attention_settings_minutes_check;
ALTER TABLE business_attention_settings ADD CONSTRAINT business_attention_settings_minutes_check
  CHECK (reply_minutes BETWEEN 0 AND 1440 AND (resume_after_minutes IS NULL OR resume_after_minutes BETWEEN 1 AND 1440));

ALTER TABLE business_members ADD COLUMN IF NOT EXISTS email TEXT;

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS customer_waiting_since TIMESTAMPTZ;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS ai_resumed_at TIMESTAMPTZ;
-- La revisión periódica busca los chats pausados con un cliente esperando.
CREATE INDEX IF NOT EXISTS conversations_waiting_idx
  ON conversations (customer_waiting_since) WHERE ai_paused AND customer_waiting_since IS NOT NULL;

ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_kind_check;
ALTER TABLE notifications ADD CONSTRAINT notifications_kind_check CHECK (kind IN ('handoff', 'ai_resumed'));

CREATE TABLE IF NOT EXISTS notification_deliveries (
  notification_id  UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
  channel          TEXT NOT NULL,
  status           TEXT NOT NULL,
  detail           TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (notification_id, channel)
);
ALTER TABLE notification_deliveries DROP CONSTRAINT IF EXISTS notification_deliveries_channel_check;
ALTER TABLE notification_deliveries ADD CONSTRAINT notification_deliveries_channel_check CHECK (channel IN ('email', 'push'));
ALTER TABLE notification_deliveries DROP CONSTRAINT IF EXISTS notification_deliveries_status_check;
ALTER TABLE notification_deliveries ADD CONSTRAINT notification_deliveries_status_check
  CHECK (status IN ('sending', 'sent', 'failed', 'skipped'));

CREATE TABLE IF NOT EXISTS push_subscriptions (
  id               UUID PRIMARY KEY,
  user_id          TEXT NOT NULL,
  endpoint         TEXT NOT NULL,
  p256dh           TEXT NOT NULL,
  auth             TEXT NOT NULL,
  device           TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_success_at  TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS push_subscriptions_endpoint_key ON push_subscriptions (endpoint);
CREATE INDEX IF NOT EXISTS push_subscriptions_user_idx ON push_subscriptions (user_id);

CREATE TABLE IF NOT EXISTS platform_keys (
  name               TEXT PRIMARY KEY,
  public_value       TEXT NOT NULL,
  secret_ciphertext  TEXT NOT NULL,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
