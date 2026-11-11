-- ============================================================================
-- 0008_business_channels.sql
--
-- Canales de cada negocio. Por ahora, WhatsApp por código QR con uazapi: el
-- servidor y el token de administrador son de la plataforma (variables de
-- entorno); aquí queda la instancia de cada negocio: el servidor donde vive, su
-- token (cifrado con la clave de los datos de pago), el estado de la conexión y el
-- identificador secreto de la ruta de su webhook. Un negocio tiene una conexión
-- por canal.
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py; una prueba comprueba que
-- ambas coinciden. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS business_channels (
  tenant_id               UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  channel                 TEXT NOT NULL,
  provider                TEXT NOT NULL,
  server_url              TEXT NOT NULL,
  token_ciphertext        TEXT NOT NULL,
  webhook_id              TEXT NOT NULL UNIQUE,
  status                  TEXT NOT NULL DEFAULT 'disconnected',
  phone                   TEXT,
  profile_name            TEXT,
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, channel)
);

COMMIT;
