-- ============================================================================
-- 0022_reply_batching.sql
--
-- Esperar a que el cliente termine de escribir (application/channels/inbound.py):
-- si manda varios mensajes seguidos, el asistente responde una sola vez a todos.
-- - reads_as: lo que lee el asistente de cada mensaje del cliente (el texto, o
--   lo que se entendió de la foto o el audio), sin datos de pago.
-- - answered_at: cuándo una respuesta del asistente lo atendió, o el equipo lo
--   tomó. El que responde reclama los pendientes en la base: ningún mensaje se
--   responde dos veces ni se queda sin respuesta, con varios servidores a la vez.
-- Aditiva. Los mensajes anteriores quedan atendidos: ninguno entra en una
-- respuesta nueva. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

ALTER TABLE conversation_entries ADD COLUMN IF NOT EXISTS reads_as TEXT;
ALTER TABLE conversation_entries ADD COLUMN IF NOT EXISTS answered_at TIMESTAMPTZ;

UPDATE conversation_entries SET answered_at = created_at WHERE author = 'customer' AND answered_at IS NULL AND created_at < now() - interval '10 minutes';

CREATE INDEX IF NOT EXISTS conversation_entries_pending_idx
    ON conversation_entries (conversation_id, created_at)
    WHERE author = 'customer' AND answered_at IS NULL;

COMMIT;
