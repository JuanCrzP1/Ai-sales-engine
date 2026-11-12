import type { AgentAuthorization } from "../../repositories/agentAuthorization";
import { toArea, type AreaPayload } from "./apiIntegrations";
import type { HttpClient } from "./httpClient";

interface PromptPayload {
  ready: boolean;
  client_name: string | null;
  redirect_host: string | null;
  message: string | null;
  redirect_to: string | null;
  areas: AreaPayload[];
}

/** `AgentAuthorization` sobre la API del panel: `/api/oauth/authorize/request` y `/decision`. */
export function createApiAgentAuthorization(http: HttpClient): AgentAuthorization {
  return {
    describe: async (params) => {
      const payload = await http.get<PromptPayload>(`/oauth/authorize/request?${new URLSearchParams(params).toString()}`);
      return payload.ready
        ? { ready: true, clientName: payload.client_name ?? "Un agente de IA", redirectHost: payload.redirect_host ?? "", areas: payload.areas.map(toArea) }
        : { ready: false, message: payload.message ?? "La solicitud no es válida.", redirectTo: payload.redirect_to };
    },
    decide: async ({ params, approve, permissions, reach, businesses }) => {
      const payload = await http.post<{ redirect_to: string }>("/oauth/authorize/decision", {
        params,
        approve,
        ...(approve ? { permissions, reach, businesses } : {}),
      });
      return payload.redirect_to;
    },
  };
}
