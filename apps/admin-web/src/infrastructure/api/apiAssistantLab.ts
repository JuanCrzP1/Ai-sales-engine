import type { AISettings, AIUsage, AssistantLab, AssistantReply, ConfigSource, KeyCheck } from "../../repositories/assistantLab";
import type { HttpClient } from "./httpClient";

interface ReplyPayload {
  session_id: string;
  source: ConfigSource;
  version: number;
  reply: string;
  intent: string | null;
  ai_answered: boolean;
}

interface UsagePayload {
  since: string;
  replies: number;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number | null;
  days: { day: string; replies: number; tokens: number }[];
}

/** `AssistantLab` sobre la API del panel: `/api/businesses/{slug}/ai` y `/api/businesses/{slug}/playground`. */
export function createApiAssistantLab(http: HttpClient, slug: string): AssistantLab {
  const base = `/businesses/${encodeURIComponent(slug)}`;
  return {
    getAISettings: () => http.get<AISettings>(`${base}/ai`),
    saveAISettings: ({ model, apiKey, clearKey }) =>
      http.put<AISettings>(`${base}/ai`, { model, ...(apiKey ? { api_key: apiKey } : {}), ...(clearKey ? { clear_key: true } : {}) }),
    verifyAIKey: () => http.post<KeyCheck>(`${base}/ai/verify`),
    async getAIUsage(): Promise<AIUsage> {
      const payload = await http.get<UsagePayload>(`${base}/ai/usage`);
      return {
        since: payload.since,
        replies: payload.replies,
        promptTokens: payload.prompt_tokens,
        completionTokens: payload.completion_tokens,
        costUsd: payload.cost_usd,
        days: payload.days,
      };
    },
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
