-- ============================================================================
-- 0007_ai_usage.sql
--
-- Consumo de inteligencia artificial de cada negocio: respuestas y tokens por día y
-- modelo, y el costo en dólares cuando OpenRouter lo informa. Cada respuesta suma a
-- su fila con un INSERT ... ON CONFLICT DO UPDATE atómico. El panel lo muestra en
-- «Inteligencia artificial».
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py; una prueba comprueba que
-- ambas coinciden. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS ai_usage (
  tenant_id          UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  day                DATE NOT NULL,
  model              TEXT NOT NULL,
  replies            INTEGER NOT NULL DEFAULT 0,
  prompt_tokens      BIGINT NOT NULL DEFAULT 0,
  completion_tokens  BIGINT NOT NULL DEFAULT 0,
  cost_usd           NUMERIC(14, 6),
  PRIMARY KEY (tenant_id, day, model)
);

COMMIT;
