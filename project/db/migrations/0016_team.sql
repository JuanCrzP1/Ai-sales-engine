-- ============================================================================
-- 0016_team.sql
--
-- El equipo de cada negocio (Configuración → Equipo):
--   · `business_members.role`: además del dueño (`owner`), el administrador
--     (`admin`) y el asesor (`agent`). Qué puede cada uno lo decide
--     `domain/business_config/team.py`.
--   · `team_invitations`: las invitaciones por enlace. Se guarda la huella
--     SHA-256 del enlace, nunca el enlace. Vencen a los 7 días; al aceptarla, la
--     persona queda en `business_members` con el rol de la invitación.
-- Se borran con el negocio (ON DELETE CASCADE). Aditiva: los dueños de hoy
-- siguen igual. La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py. Se puede aplicar más de
-- una vez.
-- ============================================================================

BEGIN;

ALTER TABLE business_members DROP CONSTRAINT IF EXISTS business_members_role_check;
ALTER TABLE business_members ADD CONSTRAINT business_members_role_check
  CHECK (role IN ('owner', 'admin', 'agent'));

CREATE TABLE IF NOT EXISTS team_invitations (
  id            UUID PRIMARY KEY,
  tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  email         TEXT NOT NULL,
  role          TEXT NOT NULL,
  token_hash    TEXT NOT NULL,
  invited_by    TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at    TIMESTAMPTZ NOT NULL,
  accepted_at   TIMESTAMPTZ,
  accepted_by   TEXT,
  revoked_at    TIMESTAMPTZ,
  CONSTRAINT team_invitations_token_unique UNIQUE (token_hash)
);

ALTER TABLE team_invitations DROP CONSTRAINT IF EXISTS team_invitations_role_check;
ALTER TABLE team_invitations ADD CONSTRAINT team_invitations_role_check
  CHECK (role IN ('owner', 'admin', 'agent'));

CREATE INDEX IF NOT EXISTS team_invitations_tenant_idx ON team_invitations (tenant_id, created_at);

COMMIT;
