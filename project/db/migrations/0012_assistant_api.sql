-- ============================================================================
-- 0012_assistant_api.sql
--
-- Integraciones:
--   · `api_keys`: las claves de API de cada negocio. Se guarda solo su huella
--     (SHA-256) y su comienzo visible para reconocerla; la clave completa se
--     muestra una sola vez. Cada una tiene sus permisos (`scopes`), quién la creó,
--     cuándo se usó por última vez y, si se revocó, cuándo.
--   · `api_idempotency`: la respuesta a cada pedido con `Idempotency-Key`, cifrada,
--     para devolver la misma si el pedido se repite (24 horas).
--   · las conversaciones pueden llegar por la API del asistente (canal `api`).
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py. Se puede aplicar más de
-- una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS api_keys (
  id            UUID PRIMARY KEY,
  tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  prefix        TEXT NOT NULL,
  key_hash      TEXT NOT NULL,
  scopes        JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_by    TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at  TIMESTAMPTZ,
  revoked_at    TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS api_keys_hash_key ON api_keys (key_hash);
CREATE INDEX IF NOT EXISTS api_keys_tenant_idx ON api_keys (tenant_id, created_at);

-- Un pedido repetido (misma `Idempotency-Key`) recibe la misma respuesta durante 24 horas. Se guarda cifrada con
-- BUSINESS_CONFIG_SECRETS_KEY: lleva lo mismo que recibió el cliente, datos de pago incluidos.
CREATE TABLE IF NOT EXISTS api_idempotency (
  tenant_id            UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  idempotency_key      TEXT NOT NULL,
  response_ciphertext  TEXT NOT NULL,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS api_idempotency_created_idx ON api_idempotency (created_at);

ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_channel_check;
ALTER TABLE conversations ADD CONSTRAINT conversations_channel_check
  CHECK (channel IN ('whatsapp', 'instagram', 'telegram', 'web', 'api', 'prueba'));

COMMIT;
