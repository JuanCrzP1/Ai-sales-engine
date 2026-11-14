-- ============================================================================
-- 0019_conversation_messages_recent.sql
--
-- La memoria del motor lee en cada mensaje los mensajes más recientes de un
-- cliente (`conversation_messages`, del esquema del motor en
-- project/docs/postgresql_schema.sql): este índice los encuentra sin recorrer
-- toda la conversación, aunque el negocio tenga miles de clientes.
-- Ver project/app/infrastructure/persistence/sql_memory.py.
-- Aditiva. Si la base todavía no tiene las tablas del motor (las crea
-- scripts/setup_cloud_database.py), no hace nada. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

DO $$
BEGIN
  IF to_regclass('public.conversation_messages') IS NOT NULL THEN
    CREATE INDEX IF NOT EXISTS conversation_messages_recent
      ON conversation_messages (tenant_id, client_id, created_at DESC);
  END IF;
END
$$;

COMMIT;
