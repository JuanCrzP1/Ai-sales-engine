-- ============================================================================
-- 0010_sales_and_stages.sql
--
-- Clientes, ventas y reportes:
--   · cada conversación guarda la etapa a la que llegó su cliente: nuevo,
--     interesado, listo para comprar, pagó (por verificar) o cliente. Solo avanza.
--   · `sales`: las ventas que registra el equipo (qué compró, cuánto y en qué
--     moneda), atadas a la conversación cuando la hay. Anular una venta la deja
--     marcada, no la borra.
-- Las etapas de las conversaciones que ya existían se calculan aquí con lo que
-- la IA reconoció en cada mensaje. La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py. Se puede aplicar más de
-- una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS sales (
  id               UUID PRIMARY KEY,
  tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  conversation_id  UUID REFERENCES conversations(id) ON DELETE SET NULL,
  customer_name    TEXT NOT NULL,
  description      TEXT NOT NULL,
  amount           NUMERIC(14, 2) NOT NULL,
  currency         TEXT NOT NULL,
  status           TEXT NOT NULL DEFAULT 'confirmed',
  created_by       TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  cancelled_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS sales_tenant_recent_idx ON sales (tenant_id, created_at);
ALTER TABLE sales DROP CONSTRAINT IF EXISTS sales_status_check;
ALTER TABLE sales ADD CONSTRAINT sales_status_check CHECK (status IN ('confirmed', 'cancelled'));

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS stage TEXT NOT NULL DEFAULT 'new';
ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_stage_check;
ALTER TABLE conversations ADD CONSTRAINT conversations_stage_check
  CHECK (stage IN ('new', 'interested', 'ready', 'payment', 'customer'));

-- Las conversaciones de antes: su etapa sale de lo que la IA reconoció (solo avanza).
UPDATE conversations c SET stage = 'interested'
  WHERE stage = 'new'
    AND EXISTS (SELECT 1 FROM conversation_entries e WHERE e.conversation_id = c.id AND e.intent IN ('pain', 'info', 'objection'));
UPDATE conversations c SET stage = 'ready'
  WHERE stage IN ('new', 'interested')
    AND EXISTS (SELECT 1 FROM conversation_entries e WHERE e.conversation_id = c.id AND e.intent = 'buy');
UPDATE conversations SET stage = 'payment' WHERE handoff_reason = 'payment_review' AND stage IN ('new', 'interested', 'ready');

COMMIT;
