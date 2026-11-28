-- ============================================================================
-- 0025_customer_pipeline.sql
--
-- El tablero de Clientes (domain/business_config/pipeline.py): el equipo mueve
-- a cada cliente de etapa a mano y puede sacarlo del embudo como «no compró».
-- - La etapa admite 'lost' (no compró), además de las cinco del embudo.
-- - lost_reason / lost_at: por qué y cuándo lo marcó el equipo. Solo valen
--   mientras la etapa siga en 'lost': si el cliente vuelve a escribir con
--   interés, el asistente lo regresa al embudo.
-- Aditiva. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS lost_reason TEXT;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS lost_at TIMESTAMPTZ;

ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_stage_check;
ALTER TABLE conversations ADD CONSTRAINT conversations_stage_check
    CHECK (stage IN ('new', 'interested', 'ready', 'payment', 'customer', 'lost'));

-- El tablero cuenta y lista los clientes de cada etapa, lo más reciente primero.
CREATE INDEX IF NOT EXISTS conversations_stage_recent_idx
    ON conversations (tenant_id, stage, last_message_at);

COMMIT;
