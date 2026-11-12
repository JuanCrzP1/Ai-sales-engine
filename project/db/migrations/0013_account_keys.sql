-- ============================================================================
-- 0013_account_keys.sql
--
-- Claves de API de la CUENTA, para los agentes de IA (servidor MCP):
--   · una clave es de quien la creó (`owner_user_id`, la cuenta de Neon Auth) y
--     entra a un negocio (`reach = 'one'`, el de `tenant_id`), a todos los de su
--     dueño (`all`, también los que cree después) o a algunos (`some`, los de
--     `api_key_businesses`);
--   · puede vencer (`expires_at`); vencida, deja de servir como una revocada.
-- Las claves que ya existían quedan como estaban: de un negocio y sin vencimiento.
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py. Se puede aplicar más de
-- una vez.
-- ============================================================================

BEGIN;

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS reach TEXT NOT NULL DEFAULT 'one';
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;
ALTER TABLE api_keys ALTER COLUMN tenant_id DROP NOT NULL;

ALTER TABLE api_keys DROP CONSTRAINT IF EXISTS api_keys_reach_check;
ALTER TABLE api_keys ADD CONSTRAINT api_keys_reach_check CHECK (
  (reach = 'one' AND tenant_id IS NOT NULL) OR (reach IN ('all', 'some') AND tenant_id IS NULL)
);

CREATE INDEX IF NOT EXISTS api_keys_owner_idx ON api_keys (owner_user_id, created_at) WHERE owner_user_id IS NOT NULL;

-- Los negocios de una clave que entra a algunos. Borrar el negocio o la clave borra la fila.
CREATE TABLE IF NOT EXISTS api_key_businesses (
  key_id     UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
  tenant_id  UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  PRIMARY KEY (key_id, tenant_id)
);
CREATE INDEX IF NOT EXISTS api_key_businesses_tenant_idx ON api_key_businesses (tenant_id);

COMMIT;
