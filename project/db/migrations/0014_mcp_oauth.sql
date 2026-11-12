-- OAuth 2.1 del servidor MCP: Claude (web y app) y ChatGPT se conectan pegando solo la dirección e iniciando sesión.
--
-- Una clave puede ser `key` (la de siempre: un valor fijo que se muestra una vez) o `oauth` (una conexión que la persona autorizó
-- desde el agente: sin valor fijo; sus tokens rotan). Los agentes se registran solos (RFC 7591). De los códigos y los tokens se
-- guarda solo la huella SHA-256; se borran con su conexión. Aditiva: las claves existentes quedan `key`.

BEGIN;

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT 'key';
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS client_id TEXT;
ALTER TABLE api_keys ALTER COLUMN key_hash DROP NOT NULL;

ALTER TABLE api_keys DROP CONSTRAINT IF EXISTS api_keys_kind_check;
ALTER TABLE api_keys ADD CONSTRAINT api_keys_kind_check CHECK (
  (kind = 'key' AND key_hash IS NOT NULL) OR (kind = 'oauth' AND key_hash IS NULL AND client_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS api_keys_client_idx ON api_keys (owner_user_id, client_id) WHERE client_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS mcp_oauth_clients (
  client_id      TEXT PRIMARY KEY,
  name           TEXT NOT NULL,
  redirect_uris  JSONB NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT mcp_oauth_clients_uris_check CHECK (jsonb_typeof(redirect_uris) = 'array')
);

CREATE TABLE IF NOT EXISTS mcp_oauth_codes (
  code_hash       TEXT PRIMARY KEY,
  client_id       TEXT NOT NULL REFERENCES mcp_oauth_clients(client_id) ON DELETE CASCADE,
  key_id          UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
  redirect_uri    TEXT NOT NULL,
  code_challenge  TEXT NOT NULL,
  resource        TEXT,
  expires_at      TIMESTAMPTZ NOT NULL,
  CONSTRAINT mcp_oauth_codes_hash_check CHECK (code_hash ~ '^[0-9a-f]{64}$')
);
CREATE INDEX IF NOT EXISTS mcp_oauth_codes_expiry_idx ON mcp_oauth_codes (expires_at);

CREATE TABLE IF NOT EXISTS mcp_oauth_tokens (
  id                  UUID PRIMARY KEY,
  key_id              UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
  client_id           TEXT NOT NULL REFERENCES mcp_oauth_clients(client_id) ON DELETE CASCADE,
  access_hash         TEXT NOT NULL,
  access_expires_at   TIMESTAMPTZ NOT NULL,
  refresh_hash        TEXT NOT NULL,
  refresh_expires_at  TIMESTAMPTZ NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT mcp_oauth_tokens_hashes_check CHECK (access_hash ~ '^[0-9a-f]{64}$' AND refresh_hash ~ '^[0-9a-f]{64}$')
);
CREATE UNIQUE INDEX IF NOT EXISTS mcp_oauth_tokens_access_key ON mcp_oauth_tokens (access_hash);
CREATE UNIQUE INDEX IF NOT EXISTS mcp_oauth_tokens_refresh_key ON mcp_oauth_tokens (refresh_hash);
CREATE INDEX IF NOT EXISTS mcp_oauth_tokens_key_idx ON mcp_oauth_tokens (key_id);
CREATE INDEX IF NOT EXISTS mcp_oauth_tokens_expiry_idx ON mcp_oauth_tokens (refresh_expires_at);

COMMIT;
