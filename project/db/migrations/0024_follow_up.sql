-- ============================================================================
-- 0024_follow_up.sql
--
-- El seguimiento a un cliente que dejó de responder (Mensajes → Seguimiento,
-- application/follow_up/follow_up_sweep.py). Por conversación:
-- - follow_up_anchor: el último mensaje del cliente al que se refieren los
--   seguimientos enviados. Si el cliente vuelve a escribir, ya no coincide y
--   la secuencia empieza de nuevo.
-- - follow_up_sent: cuántos mensajes de la secuencia pasaron (enviados o
--   saltados por viejos) desde ese mensaje del cliente.
-- - follow_up_stopped_at / follow_up_stopped_by: el seguimiento se detuvo en
--   ese chat: lo detuvo el equipo ('team') o el cliente dijo que no le
--   interesa ('customer'). No se vuelve a enviar hasta que lo reanuden.
-- Aditiva. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS follow_up_anchor TIMESTAMPTZ;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS follow_up_sent INTEGER NOT NULL DEFAULT 0;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS follow_up_stopped_at TIMESTAMPTZ;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS follow_up_stopped_by TEXT;

ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_follow_up_stopped_by_check;
ALTER TABLE conversations ADD CONSTRAINT conversations_follow_up_stopped_by_check
    CHECK (follow_up_stopped_by IS NULL OR follow_up_stopped_by IN ('team', 'customer'));

-- La revisión busca los chats de WhatsApp y Telegram con actividad reciente y el seguimiento sin detener.
CREATE INDEX IF NOT EXISTS conversations_follow_up_idx
    ON conversations (last_message_at)
    WHERE follow_up_stopped_at IS NULL AND channel IN ('whatsapp', 'telegram');

COMMIT;
