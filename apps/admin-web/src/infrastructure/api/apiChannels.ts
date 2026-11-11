import type { Channels, WhatsAppChannel, WhatsAppStatus } from "../../repositories/channels";
import type { HttpClient } from "./httpClient";

interface WhatsAppPayload {
  available: boolean;
  status: WhatsAppStatus;
  phone: string | null;
  profile_name: string | null;
  qrcode: string | null;
  paircode: string | null;
}

function toWhatsApp(payload: WhatsAppPayload): WhatsAppChannel {
  return {
    available: payload.available,
    status: payload.status,
    phone: payload.phone,
    profileName: payload.profile_name,
    qrcode: payload.qrcode,
    paircode: payload.paircode,
  };
}

/** `Channels` sobre la API del panel: `/api/businesses/{slug}/channels/whatsapp`. */
export function createApiChannels(http: HttpClient, slug: string): Channels {
  const base = `/businesses/${encodeURIComponent(slug)}/channels/whatsapp`;
  return {
    whatsapp: async () => toWhatsApp(await http.get<WhatsAppPayload>(base)),
    connectWhatsApp: async () => toWhatsApp(await http.post<WhatsAppPayload>(`${base}/connect`)),
    newWhatsAppCode: async () => toWhatsApp(await http.post<WhatsAppPayload>(`${base}/new-code`)),
    whatsAppStatus: async () => toWhatsApp(await http.get<WhatsAppPayload>(`${base}/status`)),
    disconnectWhatsApp: async () => toWhatsApp(await http.post<WhatsAppPayload>(`${base}/disconnect`)),
  };
}
