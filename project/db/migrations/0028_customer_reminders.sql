-- ============================================================================
-- 0028_customer_reminders.sql
--
-- Los recordatorios del equipo (domain/business_config/reminders.py): qué
-- hacer con un cliente y cuándo, para quién del equipo (assignee_id, su
-- user_id) y si ya se hizo (done_at, done_by). Se borran con el cliente
-- (su conversación) y con el negocio.
-- Aditiva. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS customer_reminders (
  id               UUID PRIMARY KEY,
  tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  title            TEXT NOT NULL,
  due_at           TIMESTAMPTZ NOT NULL,
  assignee_id      TEXT,
  created_by       TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  done_at          TIMESTAMPTZ,
  done_by          TEXT
);

-- Los pendientes de un negocio por fecha, y los de cada cliente.
CREATE INDEX IF NOT EXISTS customer_reminders_open_idx ON customer_reminders (tenant_id, done_at, due_at);
CREATE INDEX IF NOT EXISTS customer_reminders_conversation_idx ON customer_reminders (conversation_id, due_at);

COMMIT;
