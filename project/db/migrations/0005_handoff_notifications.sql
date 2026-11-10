-- ============================================================================
-- 0005_handoff_notifications.sql
--
-- Pasar a una persona: la conversación queda marcada mientras espera a alguien del
-- equipo (`needs_human`, desde `handoff_requested_at`) y el negocio recibe un aviso
-- en `notifications`. Cada persona marca como leídos los suyos en
-- `notification_reads` (`user_id` es el usuario de Neon Auth).
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py; una prueba comprueba que
-- ambas coinciden. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS needs_human BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS handoff_requested_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS notifications (
  id               UUID PRIMARY KEY,
  tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  conversation_id  UUID REFERENCES conversations(id) ON DELETE CASCADE,
  kind             TEXT NOT NULL,
  title            TEXT NOT NULL,
  body             TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT notifications_kind_check CHECK (kind IN ('handoff'))
);

CREATE INDEX IF NOT EXISTS notifications_tenant_recent_idx ON notifications (tenant_id, created_at);

CREATE TABLE IF NOT EXISTS notification_reads (
  notification_id  UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
  user_id          TEXT NOT NULL,
  read_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (notification_id, user_id)
);

COMMIT;
