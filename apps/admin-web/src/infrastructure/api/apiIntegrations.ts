import type { AccessLevel, KeyArea, KeyReach } from "../../domain/integrations/types";
import type { ApiKey, AssistantApiReply, Integrations, IntegrationsOverview } from "../../repositories/integrations";
import type { HttpClient } from "./httpClient";

interface ApiKeyPayload {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  permissions: Record<string, AccessLevel>;
  reach: KeyReach;
  businesses: string[];
  created_at: string;
  created_by: string | null;
  last_used_at: string | null;
  revoked_at: string | null;
  expires_at: string | null;
  active: boolean;
  expired: boolean;
}

interface OverviewPayload {
  assistant_api: { url: string | null; chat_keys: number };
  api_keys: { active: number };
  mcp: { url: string | null };
  areas: { id: string; label: string; read: string | null; write: string | null; one_business_only: boolean }[];
}

function toKey(payload: ApiKeyPayload): ApiKey {
  return {
    id: payload.id,
    name: payload.name,
    prefix: payload.prefix,
    scopes: payload.scopes,
    permissions: payload.permissions,
    reach: payload.reach,
    businesses: payload.businesses,
    createdAt: payload.created_at,
    createdBy: payload.created_by,
    lastUsedAt: payload.last_used_at,
    revokedAt: payload.revoked_at,
    expiresAt: payload.expires_at,
    active: payload.active,
    expired: payload.expired,
  };
}

function toArea(payload: OverviewPayload["areas"][number]): KeyArea {
  return { id: payload.id, label: payload.label, read: payload.read, write: payload.write, oneBusinessOnly: payload.one_business_only };
}

function toOverview(payload: OverviewPayload): IntegrationsOverview {
  return {
    assistantApiUrl: payload.assistant_api.url,
    mcpUrl: payload.mcp.url,
    chatKeys: payload.assistant_api.chat_keys,
    activeKeys: payload.api_keys.active,
    areas: payload.areas.map(toArea),
  };
}

/** `Integrations` sobre la API del panel: `/api/businesses/{slug}/integrations` y `/api-keys`. */
export function createApiIntegrations(http: HttpClient, slug: string): Integrations {
  const base = `/businesses/${encodeURIComponent(slug)}`;
  return {
    overview: async () => toOverview(await http.get<OverviewPayload>(`${base}/integrations`)),
    keys: async () => (await http.get<ApiKeyPayload[]>(`${base}/api-keys`)).map(toKey),
    createKey: async ({ name, permissions, reach, businesses, expiresInDays }) => {
      const created = await http.post<ApiKeyPayload & { secret: string }>(`${base}/api-keys`, {
        name,
        permissions,
        reach,
        ...(reach === "some" ? { businesses } : {}),
        expires_in_days: expiresInDays,
      });
      return { key: toKey(created), secret: created.secret };
    },
    revokeKey: async (id) => toKey(await http.post<ApiKeyPayload>(`${base}/api-keys/${encodeURIComponent(id)}/revoke`)),
    tryAssistantApi: async (message) => http.post<AssistantApiReply>(`${base}/integrations/assistant-api/try`, { message }),
  };
}
