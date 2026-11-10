import type { AISettings, AssistantLab, AssistantReply, ConfigSource, KeyCheck } from "../../repositories/assistantLab";
import type { HttpClient } from "./httpClient";

interface ReplyPayload {
  session_id: string;
  source: ConfigSource;
  version: number;
  reply: string;
  intent: string | null;
  ai_answered: boolean;
}

/** `AssistantLab` sobre la API del panel: `/api/businesses/{slug}/ai` y `/api/businesses/{slug}/playground`. */
export function createApiAssistantLab(http: HttpClient, slug: string): AssistantLab {
  const base = `/businesses/${encodeURIComponent(slug)}`;
  return {
    getAISettings: () => http.get<AISettings>(`${base}/ai`),
    saveAISettings: ({ model, apiKey, clearKey }) =>
      http.put<AISettings>(`${base}/ai`, { model, ...(apiKey ? { api_key: apiKey } : {}), ...(clearKey ? { clear_key: true } : {}) }),
    verifyAIKey: () => http.post<KeyCheck>(`${base}/ai/verify`),
    async sendMessage({ message, source, sessionId }): Promise<AssistantReply> {
      const payload = await http.post<ReplyPayload>(`${base}/playground`, { message, source, ...(sessionId ? { session_id: sessionId } : {}) });
      return {
        sessionId: payload.session_id,
        source: payload.source,
        version: payload.version,
        reply: payload.reply,
        intent: payload.intent,
        aiAnswered: payload.ai_answered,
      };
    },
    resetConversation: (sessionId) => http.delete(`${base}/playground/${encodeURIComponent(sessionId)}`),
  };
}
