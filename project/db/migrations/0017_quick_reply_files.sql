-- ============================================================================
-- 0017_quick_reply_files.sql
--
-- Los archivos de las respuestas rápidas (una foto, un PDF, un video...): se
-- suben una vez en Configuración → Respuestas rápidas y salen en el chat cada
-- vez que alguien del equipo usa la respuesta. Cada respuesta los nombra en sus
-- mensajes (`quick_replies.pieces`: {"kind": "file", "file_id": ...}). Hasta
-- 4 MB cada uno y 200 por negocio (`domain/business_config/quick_replies.py`).
-- Los que ninguna respuesta usa se borran solos después de una hora.
-- Se borran con el negocio (ON DELETE CASCADE). Aditiva. La misma definición,
-- para SQLAlchemy, está en project/app/infrastructure/business_config/tables.py.
-- Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS quick_reply_files (
  id           UUID PRIMARY KEY,
  tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  mime_type    TEXT NOT NULL,
  size_bytes   INTEGER NOT NULL,
  file_name    TEXT,
  content      BYTEA NOT NULL,
  created_by   TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE quick_reply_files DROP CONSTRAINT IF EXISTS quick_reply_files_size_check;
ALTER TABLE quick_reply_files ADD CONSTRAINT quick_reply_files_size_check CHECK (size_bytes BETWEEN 1 AND 4194304);

CREATE INDEX IF NOT EXISTS quick_reply_files_tenant_idx ON quick_reply_files (tenant_id, created_at);

COMMIT;
