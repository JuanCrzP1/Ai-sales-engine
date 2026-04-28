CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- TENANTS (AGREGAMOS SLUG)
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- SUBSCRIPTIONS
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  plan_code TEXT,
  status TEXT,
  current_period_end TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- USAGE (AGREGAMOS FK)
CREATE TABLE usage_daily (
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  date DATE,
  messages_count INT DEFAULT 0,
  ai_calls INT DEFAULT 0,
  PRIMARY KEY (tenant_id, date)
);

-- ADMIN USERS
CREATE TABLE admin_users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  email TEXT UNIQUE,
  password_hash TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- CLIENTES
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  external_id TEXT,
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
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

-- SECRETOS
CREATE TABLE tenant_secrets (
  tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  encrypted_data JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- CANALES
CREATE TABLE tenant_channels (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  channel TEXT,
  config JSONB,
  is_active BOOLEAN DEFAULT true
);

-- SETTINGS
CREATE TABLE tenant_settings (
  tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  settings JSONB
);

-- ÍNDICES (MEJORADOS)
CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_subscriptions_tenant_status ON subscriptions(tenant_id, status);
CREATE INDEX idx_clients_tenant ON clients(tenant_id);
CREATE INDEX idx_messages_tenant_client ON conversation_messages(tenant_id, client_id);
CREATE INDEX idx_usage_tenant_date ON usage_daily(tenant_id, date);
CREATE INDEX idx_memory_tenant_client ON conversation_memory(tenant_id, client_id);