-- ============================================================================
-- 0002_business_ai_settings.sql
--
-- Inteligencia artificial de cada negocio: el modelo de su asistente y su propia
-- clave de OpenRouter, cifrada con la misma clave que los datos de pago
-- (BUSINESS_CONFIG_SECRETS_KEY). No es parte del contrato comercial.
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py; una prueba comprueba que
-- ambas coinciden. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS business_ai_settings (
  tenant_id      UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  provider       TEXT NOT NULL,
  model          TEXT,
  key_ciphertext TEXT,
  key_hint       TEXT,
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
