import type { TelegramChannel, WhatsAppChannel } from "../domain/channels/types";

export type { TelegramChannel, WhatsAppChannel, WhatsAppStatus } from "../domain/channels/types";

/** Los canales de un negocio. Los fallos se rechazan con `PersistenceError`, con un mensaje para el negocio. */
export interface Channels {
  whatsapp(): Promise<WhatsAppChannel>;
  /** Prepara la conexión del negocio y trae el código QR para escanear. */
  connectWhatsApp(): Promise<WhatsAppChannel>;
  /** Un código QR nuevo (el anterior venció). */
  newWhatsAppCode(): Promise<WhatsAppChannel>;
  /** El estado actual; mientras conecta, el QR vigente. */
  whatsAppStatus(): Promise<WhatsAppChannel>;
  /** Desconecta el número y borra su conexión. */
  disconnectWhatsApp(): Promise<WhatsAppChannel>;
  telegram(): Promise<TelegramChannel>;
  /** Conecta el bot con el código de @BotFather (o lo cambia). Si el código no sirve, el error lo dice en el campo `token`. */
  connectTelegram(token: string): Promise<TelegramChannel>;
  /** Vuelve a traer aquí los mensajes del bot guardado. */
  reconnectTelegram(): Promise<TelegramChannel>;
  /** Pregunta a Telegram si el bot sigue recibiendo los mensajes aquí. */
  checkTelegram(): Promise<TelegramChannel>;
  /** El bot deja de enviar mensajes aquí. Los chats se quedan. */
  disconnectTelegram(): Promise<TelegramChannel>;
}
