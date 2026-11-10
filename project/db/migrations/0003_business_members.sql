-- ============================================================================
-- 0003_business_members.sql
--
-- Quién es miembro de cada negocio. `user_id` es el identificador del usuario en
-- Neon Auth (`neon_auth.user`). La API de la nube solo deja a cada persona llegar
-- a los negocios donde figura aquí: un negocio nunca se cruza entre usuarios.
-- Quien crea un negocio queda como su dueño en la misma transacción.
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py; una prueba comprueba que
-- ambas coinciden. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS business_members (
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id     TEXT NOT NULL,
  role        TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, user_id),
  CONSTRAINT business_members_role_check CHECK (role IN ('owner'))
);

CREATE INDEX IF NOT EXISTS business_members_user_idx ON business_members (user_id);

COMMIT;
