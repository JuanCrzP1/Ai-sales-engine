-- ============================================================================
-- 0026_customer_card.sql
--
-- La ficha del cliente (domain/business_config/customer_card.py).
-- - conversations.deal_amount / deal_currency: cuánto vale lo que el cliente
--   podría comprar. Suma en «por cerrar» mientras siga en el embudo.
-- - conversations.owner_id: quién del equipo lo atiende (su user_id).
-- - conversations.stage_changed_at: desde cuándo está en su etapa.
-- - customer_events: el historial. Cada cambio de etapa, de valor y de
--   responsable, con quién lo hizo (el asistente, alguien del equipo o una
--   venta registrada).
-- - customer_notes: las notas del equipo sobre el cliente.
-- Las dos tablas se borran con la conversación y con el negocio.
-- Aditiva. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS deal_amount NUMERIC(14, 2);
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS deal_currency TEXT;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS owner_id TEXT;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS stage_changed_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS customer_events (
  id               UUID PRIMARY KEY,
  tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  kind             TEXT NOT NULL,
  source           TEXT NOT NULL,
  from_stage       TEXT,
  to_stage         TEXT,
  detail           TEXT,
  actor            TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS customer_events_conversation_idx ON customer_events (conversation_id, created_at);
ALTER TABLE customer_events DROP CONSTRAINT IF EXISTS customer_events_kind_check;
ALTER TABLE customer_events ADD CONSTRAINT customer_events_kind_check CHECK (kind IN ('stage', 'value', 'owner'));
ALTER TABLE customer_events DROP CONSTRAINT IF EXISTS customer_events_source_check;
ALTER TABLE customer_events ADD CONSTRAINT customer_events_source_check CHECK (source IN ('assistant', 'team', 'sale'));

CREATE TABLE IF NOT EXISTS customer_notes (
  id               UUID PRIMARY KEY,
  tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  body             TEXT NOT NULL,
  author           TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS customer_notes_conversation_idx ON customer_notes (conversation_id, created_at);

COMMIT;
