-- ============================================================================
-- 0027_customer_labels.sql
--
-- Las etiquetas de los clientes (domain/business_config/customer_labels.py).
-- - customer_labels: el catálogo de cada negocio. name_key es cómo se lee el
--   nombre (sin mayúsculas ni acentos): no hay dos con la misma en un negocio.
-- - conversation_labels: las etiquetas que lleva cada cliente.
-- Se borran con el negocio; las de un cliente, con su conversación; y al
-- borrar una etiqueta, sus clientes solo la pierden.
-- Aditiva. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS customer_labels (
  id          UUID PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  name_key    TEXT NOT NULL,
  color       TEXT NOT NULL DEFAULT 'slate',
  created_by  TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE customer_labels DROP CONSTRAINT IF EXISTS customer_labels_name_key;
ALTER TABLE customer_labels ADD CONSTRAINT customer_labels_name_key UNIQUE (tenant_id, name_key);

CREATE TABLE IF NOT EXISTS conversation_labels (
  conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  label_id         UUID NOT NULL REFERENCES customer_labels(id) ON DELETE CASCADE,
  tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (conversation_id, label_id)
);

CREATE INDEX IF NOT EXISTS conversation_labels_label_idx ON conversation_labels (label_id);

COMMIT;
