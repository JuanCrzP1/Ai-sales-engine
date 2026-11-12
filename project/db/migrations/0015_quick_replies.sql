-- ============================================================================
-- 0015_quick_replies.sql
--
-- Respuestas rápidas (Configuración → Respuestas rápidas): los mensajes
-- guardados de cada negocio que el equipo pone en un chat sin copiar y pegar.
--   · `shortcut`: el atajo («precios», se busca con «/precios»), único en el
--     negocio. Lo valida y normaliza `domain/business_config/quick_replies.py`.
--   · `category`: opcional («Precios», «Pagos»…).
--   · `pieces`: los mensajes, en orden (de 1 a 10 textos).
--   · `use_count` y `last_used_at`: las más usadas salen primero en el chat.
-- Se borran con el negocio (ON DELETE CASCADE). Aditiva: no toca nada existente.
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py. Se puede aplicar más de
-- una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS quick_replies (
  id            UUID PRIMARY KEY,
  tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  shortcut      TEXT NOT NULL,
  category      TEXT,
  pieces        JSONB NOT NULL,
  use_count     INTEGER NOT NULL DEFAULT 0,
  last_used_at  TIMESTAMPTZ,
  created_by    TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT quick_replies_shortcut_unique UNIQUE (tenant_id, shortcut)
);

ALTER TABLE quick_replies DROP CONSTRAINT IF EXISTS quick_replies_shortcut_check;
ALTER TABLE quick_replies ADD CONSTRAINT quick_replies_shortcut_check
  CHECK (shortcut ~ '^[a-z0-9_-][a-z0-9 _-]{0,39}$');
ALTER TABLE quick_replies DROP CONSTRAINT IF EXISTS quick_replies_category_check;
ALTER TABLE quick_replies ADD CONSTRAINT quick_replies_category_check
  CHECK (category IS NULL OR char_length(category) BETWEEN 1 AND 40);
ALTER TABLE quick_replies DROP CONSTRAINT IF EXISTS quick_replies_pieces_check;
ALTER TABLE quick_replies ADD CONSTRAINT quick_replies_pieces_check
  CHECK (jsonb_typeof(pieces) = 'array');
ALTER TABLE quick_replies DROP CONSTRAINT IF EXISTS quick_replies_use_count_check;
ALTER TABLE quick_replies ADD CONSTRAINT quick_replies_use_count_check CHECK (use_count >= 0);

CREATE INDEX IF NOT EXISTS quick_replies_tenant_idx ON quick_replies (tenant_id, category, shortcut);

COMMIT;
