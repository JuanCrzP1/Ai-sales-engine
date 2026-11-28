-- ============================================================================
-- 0030_customer_fields.sql
--
-- Los campos del cliente (domain/business_config/customer_fields.py).
-- - customer_fields: el catálogo de cada negocio. name_key es cómo se lee el
--   nombre (sin mayúsculas ni acentos): no hay dos con la misma en un negocio.
--   kind es el tipo (no cambia) y options, las opciones de una lista.
-- - customer_field_values: el valor de cada campo en cada cliente, en su
--   forma única, con quién lo puso y cuándo.
-- Se borran con el negocio; los valores de un cliente, con su conversación;
-- y al borrar un campo, sus valores.
-- Aditiva. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS customer_fields (
  id          UUID PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  name_key    TEXT NOT NULL,
  kind        TEXT NOT NULL,
  options     JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_by  TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE customer_fields DROP CONSTRAINT IF EXISTS customer_fields_name_key;
ALTER TABLE customer_fields ADD CONSTRAINT customer_fields_name_key UNIQUE (tenant_id, name_key);
ALTER TABLE customer_fields DROP CONSTRAINT IF EXISTS customer_fields_kind_check;
ALTER TABLE customer_fields ADD CONSTRAINT customer_fields_kind_check CHECK (kind IN ('text', 'number', 'date', 'yes_no', 'choice'));

CREATE TABLE IF NOT EXISTS customer_field_values (
  conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  field_id         UUID NOT NULL REFERENCES customer_fields(id) ON DELETE CASCADE,
  tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  value            TEXT NOT NULL,
  updated_by       TEXT,
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (conversation_id, field_id)
);

CREATE INDEX IF NOT EXISTS customer_field_values_field_idx ON customer_field_values (field_id);

COMMIT;
