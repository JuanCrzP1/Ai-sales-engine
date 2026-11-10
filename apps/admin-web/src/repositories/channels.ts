import type { WhatsAppChannel } from "../domain/channels/types";

export type { WhatsAppChannel, WhatsAppStatus } from "../domain/channels/types";

/** Los canales de un negocio. Los fallos se rechazan con `PersistenceError` (un dato rechazado trae su campo en `problems`). */
export interface Channels {
  whatsapp(): Promise<WhatsAppChannel>;
  /** Guarda el servidor y el token (de la instancia o de administrador); el token nunca vuelve. */
  saveWhatsApp(input: { serverUrl: string; token: string }): Promise<WhatsAppChannel>;
  /** Pide el código QR y registra el webhook del negocio. */
  connectWhatsApp(): Promise<WhatsAppChannel>;
  /** El estado actual en el servidor; mientras conecta, el QR vigente. */
  whatsAppStatus(): Promise<WhatsAppChannel>;
  disconnectWhatsApp(): Promise<WhatsAppChannel>;
  /** Desconecta y borra la conexión con sus tokens. */
  removeWhatsApp(): Promise<void>;
}
