import type { ApiKey, AssistantApiReply, Integrations, IntegrationsOverview } from "../../repositories/integrations";
import type { HttpClient } from "./httpClient";

interface ApiKeyPayload {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  created_at: string;
  created_by: string | null;
  last_used_at: string | null;
  revoked_at: string | null;
  active: boolean;
}

interface OverviewPayload {
  assistant_api: { url: string | null; chat_keys: number };
  api_keys: { active: number };
  scopes: { id: string; label: string }[];
}

function toKey(payload: ApiKeyPayload): ApiKey {
  return {
    id: payload.id,
    name: payload.name,
    prefix: payload.prefix,
    scopes: payload.scopes,
    createdAt: payload.created_at,
    createdBy: payload.created_by,
    lastUsedAt: payload.last_used_at,
    revokedAt: payload.revoked_at,
    active: payload.active,
  };
}

function toOverview(payload: OverviewPayload): IntegrationsOverview {
  return { assistantApiUrl: payload.assistant_api.url, chatKeys: payload.assistant_api.chat_keys, activeKeys: payload.api_keys.active, scopes: payload.scopes };
}

/** `Integrations` sobre la API del panel: `/api/businesses/{slug}/integrations` y `/api-keys`. */
export function createApiIntegrations(http: HttpClient, slug: string): Integrations {
  const base = `/businesses/${encodeURIComponent(slug)}`;
  return {
    overview: async () => toOverview(await http.get<OverviewPayload>(`${base}/integrations`)),
    keys: async () => (await http.get<ApiKeyPayload[]>(`${base}/api-keys`)).map(toKey),
    createKey: async (name, scopes) => {
      const created = await http.post<ApiKeyPayload & { secret: string }>(`${base}/api-keys`, { name, scopes });
      return { key: toKey(created), secret: created.secret };
    },
    revokeKey: async (id) => toKey(await http.post<ApiKeyPayload>(`${base}/api-keys/${encodeURIComponent(id)}/revoke`)),
    tryAssistantApi: async (message) => http.post<AssistantApiReply>(`${base}/integrations/assistant-api/try`, { message }),
  };
}
