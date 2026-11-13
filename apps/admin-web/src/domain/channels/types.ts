/** Estado de la conexión de WhatsApp de un negocio. */
export type WhatsAppStatus = "disconnected" | "connecting" | "connected";

/**
 * La conexión de WhatsApp por código QR de un negocio, tal como la muestra el panel. El servidor y los tokens son de la plataforma:
 * nunca llegan aquí.
 */
export interface WhatsAppChannel {
  /** Si la plataforma tiene activa la conexión por código QR. */
  available: boolean;
  status: WhatsAppStatus;
  phone: string | null;
  profileName: string | null;
  /** El código QR para escanear (imagen en `data:`), solo mientras se conecta. */
  qrcode: string | null;
  paircode: string | null;
}

/** Dónde crea el negocio su bot de Telegram (y pide un código nuevo con /token). */
export const BOTFATHER_URL = "https://t.me/BotFather";

/**
 * El bot de Telegram de un negocio, tal como lo muestra el panel. El código (token) solo viaja una vez, al conectar: nunca vuelve.
 * `disconnected` con un bot guardado quiere decir que dejó de recibir los mensajes aquí (`problem` dice por qué).
 */
export interface TelegramChannel {
  /** Si la plataforma tiene activo Telegram (necesita su dirección pública). */
  available: boolean;
  status: "connected" | "disconnected";
  botUsername: string | null;
  botName: string | null;
  /** El enlace para que los clientes abran el chat: https://t.me/usuario. */
  link: string | null;
  problem: string | null;
}
