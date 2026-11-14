-- ============================================================================
-- 0021_notification_note.sql
--
-- Un aviso al equipo puede llevar lo que escribió el cliente o la nota que la
-- IA escribió para el equipo (application/pipeline/handoff_brief.py). La
-- campana y el correo citan entre comillas solo lo que escribió el cliente:
-- la nota no son palabras suyas.
-- Aditiva: los avisos anteriores quedan como lo que escribió el cliente. Se
-- puede aplicar más de una vez.
-- ============================================================================

BEGIN;

ALTER TABLE notifications ADD COLUMN IF NOT EXISTS body_is_note BOOLEAN NOT NULL DEFAULT false;

COMMIT;
