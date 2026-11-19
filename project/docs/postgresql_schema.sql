CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- TENANTS (AGREGAMOS SLUG)
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Suscripciones, planes y límites de uso pertenecen a la plataforma externa:
-- el motor no define ni consulta tablas para ello.
-- Las tablas del sistema anterior (admin_users, tenant_secrets, tenant_channels,
-- tenant_settings) se retiraron: project/db/migrations/0023_retire_legacy_tables.sql.

-- CLIENTES
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  external_id TEXT,
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, external_id)
);

-- MENSAJES (AGREGAMOS FK)
CREATE TABLE conversation_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
  role TEXT,
  content TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- MEMORIA (AGREGAMOS FK)
CREATE TABLE conversation_memory (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
  memory JSONB,
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, client_id)
);

-- ÍNDICES (MEJORADOS)
CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_clients_tenant ON clients(tenant_id);
CREATE INDEX idx_messages_tenant_client ON conversation_messages(tenant_id, client_id);
CREATE INDEX idx_memory_tenant_client ON conversation_memory(tenant_id, client_id);