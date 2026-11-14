-- ============================================================================
-- 0020_handoff_summary.sql
--
-- Cuando un chat pasa a una persona, la IA escribe para el equipo quién es el
-- cliente y qué necesita (application/pipeline/handoff_brief.py). Se guarda en
-- la conversación para mostrarlo en el chat del panel y se borra con «Ya lo
-- atendí», junto con el motivo.
-- Aditiva: sin la nota, el aviso lleva el último mensaje del cliente, como
-- antes. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS handoff_summary TEXT;

COMMIT;
