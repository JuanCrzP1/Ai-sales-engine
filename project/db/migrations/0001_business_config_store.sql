-- ============================================================================
-- 0001_business_config_store.sql
--
-- ESTADO: PREPARADA PARA REVISIÓN. NO EJECUTADA EN NINGUNA BASE DE DATOS.
-- Aplicarla primero en una rama de Neon, nunca directamente en producción.
--
-- Almacén versionado de la configuración comercial de cada negocio (contrato
-- BusinessConfig v1, ver docs/business-config.md) y de sus datos de pago cifrados.
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/config/business_config_tables.py; una prueba
-- comprueba que ambas coinciden.
--
-- Identificadores: UUID es el identificador canónico de los negocios, igual que
-- en project/docs/postgresql_schema.sql y en la ruta conversacional en ejecución
-- (tenant_channel_resolver, DBRepository, memory_repository). Requiere la tabla
-- `tenants (id UUID PRIMARY KEY, slug TEXT UNIQUE)` de ese esquema. Los modelos
-- ORM con ids enteros (project/app/models) no participan.
--
-- Separación de responsabilidades: aquí solo hay configuración comercial y datos
-- de pago. Las credenciales de canales (WhatsApp, Telegram...) siguen en
-- `tenant_secrets`, que pertenece a las integraciones.
--
-- Ciclo de vida: cada guardado crea una versión `draft` inmutable y validada;
-- publicar archiva la versión `published` y publica otra en una transacción;
-- revertir vuelve a publicar la versión publicada anterior.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS business_configs (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id      UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  version        INTEGER NOT NULL,
  schema_version TEXT NOT NULL,
  status         TEXT NOT NULL,
  document       JSONB NOT NULL,
  content_hash   TEXT NOT NULL,
  created_by     TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at   TIMESTAMPTZ,
  UNIQUE (tenant_id, version),
  CONSTRAINT business_configs_version_positive CHECK (version > 0),
  CONSTRAINT business_configs_status CHECK (status IN ('draft', 'published', 'archived'))
);

-- Como máximo una versión publicada (activa) por negocio.
CREATE UNIQUE INDEX IF NOT EXISTS business_configs_one_published
  ON business_configs (tenant_id)
  WHERE status = 'published';

-- Datos de pago referenciados desde el documento con
-- {"secret_ref": "secret_store:<ref_key>"}. La aplicación los cifra (Fernet, clave
-- BUSINESS_CONFIG_SECRETS_KEY) antes de enviarlos: la base de datos nunca recibe
-- el texto plano.
CREATE TABLE IF NOT EXISTS business_config_secrets (
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  ref_key     TEXT NOT NULL,
  ciphertext  TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, ref_key)
);

COMMIT;

-- Reversión (solo en una base de pruebas, nunca con datos en uso):
--   DROP TABLE IF EXISTS business_config_secrets;
--   DROP TABLE IF EXISTS business_configs;
