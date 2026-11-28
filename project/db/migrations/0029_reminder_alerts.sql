-- ============================================================================
-- 0029_reminder_alerts.sql
--
-- Los recordatorios avisan cuando llega su hora (application/attention/
-- reminder_sweep.py): un aviso de tipo 'reminder' en la campana y en el
-- celular de su responsable.
--
-- - notifications.recipient_id: para quién es un aviso (su user_id). Vacío,
--   para todo el equipo del negocio, como los avisos de antes.
-- - customer_reminders.notified_at: cuándo se avisó. Cada recordatorio avisa
--   una sola vez aunque dos revisiones corran a la vez.
-- Aditiva. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

ALTER TABLE notifications ADD COLUMN IF NOT EXISTS recipient_id TEXT;

ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_kind_check;
ALTER TABLE notifications ADD CONSTRAINT notifications_kind_check CHECK (kind IN ('handoff', 'ai_resumed', 'reminder'));

ALTER TABLE customer_reminders ADD COLUMN IF NOT EXISTS notified_at TIMESTAMPTZ;

-- Los recordatorios pendientes que aún no avisaron, por hora: lo que busca la revisión.
CREATE INDEX IF NOT EXISTS customer_reminders_due_idx
  ON customer_reminders (due_at) WHERE done_at IS NULL AND notified_at IS NULL;

COMMIT;
