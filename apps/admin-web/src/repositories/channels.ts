import type { WhatsAppChannel } from "../domain/channels/types";

export type { WhatsAppChannel, WhatsAppStatus } from "../domain/channels/types";

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
}
