import type { Channels, TelegramChannel, WhatsAppChannel, WhatsAppStatus } from "../../repositories/channels";
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

interface TelegramPayload {
  available: boolean;
  status: TelegramChannel["status"];
  bot_username: string | null;
  bot_name: string | null;
  link: string | null;
  problem: string | null;
}

function toTelegram(payload: TelegramPayload): TelegramChannel {
  return {
    available: payload.available,
    status: payload.status,
    botUsername: payload.bot_username,
    botName: payload.bot_name,
    link: payload.link,
    problem: payload.problem,
  };
}

/** `Channels` sobre la API del panel: `/api/businesses/{slug}/channels/whatsapp` y `/channels/telegram`. */
export function createApiChannels(http: HttpClient, slug: string): Channels {
  const base = `/businesses/${encodeURIComponent(slug)}/channels/whatsapp`;
  const bot = `/businesses/${encodeURIComponent(slug)}/channels/telegram`;
  return {
    whatsapp: async () => toWhatsApp(await http.get<WhatsAppPayload>(base)),
    connectWhatsApp: async () => toWhatsApp(await http.post<WhatsAppPayload>(`${base}/connect`)),
    newWhatsAppCode: async () => toWhatsApp(await http.post<WhatsAppPayload>(`${base}/new-code`)),
    whatsAppStatus: async () => toWhatsApp(await http.get<WhatsAppPayload>(`${base}/status`)),
    disconnectWhatsApp: async () => toWhatsApp(await http.post<WhatsAppPayload>(`${base}/disconnect`)),
    telegram: async () => toTelegram(await http.get<TelegramPayload>(bot)),
    connectTelegram: async (token) => toTelegram(await http.post<TelegramPayload>(`${bot}/connect`, { token })),
    reconnectTelegram: async () => toTelegram(await http.post<TelegramPayload>(`${bot}/reconnect`)),
    checkTelegram: async () => toTelegram(await http.get<TelegramPayload>(`${bot}/status`)),
    disconnectTelegram: async () => toTelegram(await http.post<TelegramPayload>(`${bot}/disconnect`)),
  };
}
