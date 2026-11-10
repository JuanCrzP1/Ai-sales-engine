import type { Channels, WhatsAppChannel, WhatsAppStatus } from "../../repositories/channels";
import type { HttpClient } from "./httpClient";

interface WhatsAppPayload {
  configured: boolean;
  provider: string | null;
  server_url: string | null;
  status: WhatsAppStatus;
  token_hint: string | null;
  has_admin_token: boolean;
  phone: string | null;
  profile_name: string | null;
  webhook_ready: boolean;
  qrcode: string | null;
  paircode: string | null;
}

function toWhatsApp(payload: WhatsAppPayload): WhatsAppChannel {
  return {
    configured: payload.configured,
    provider: payload.provider,
    serverUrl: payload.server_url,
    status: payload.status,
    tokenHint: payload.token_hint,
    hasAdminToken: payload.has_admin_token,
    phone: payload.phone,
    profileName: payload.profile_name,
    webhookReady: payload.webhook_ready,
    qrcode: payload.qrcode,
    paircode: payload.paircode,
  };
}

/** `Channels` sobre la API del panel: `/api/businesses/{slug}/channels/whatsapp`. */
export function createApiChannels(http: HttpClient, slug: string): Channels {
  const base = `/businesses/${encodeURIComponent(slug)}/channels/whatsapp`;
  return {
    whatsapp: async () => toWhatsApp(await http.get<WhatsAppPayload>(base)),
    saveWhatsApp: async ({ serverUrl, token }) => toWhatsApp(await http.put<WhatsAppPayload>(base, { server_url: serverUrl, token })),
    connectWhatsApp: async () => toWhatsApp(await http.post<WhatsAppPayload>(`${base}/connect`)),
    whatsAppStatus: async () => toWhatsApp(await http.get<WhatsAppPayload>(`${base}/status`)),
    disconnectWhatsApp: async () => toWhatsApp(await http.post<WhatsAppPayload>(`${base}/disconnect`)),
    removeWhatsApp: () => http.delete(base),
  };
}
