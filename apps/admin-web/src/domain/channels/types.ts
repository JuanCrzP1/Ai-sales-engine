/** Estado de la conexión de WhatsApp de un negocio. */
export type WhatsAppStatus = "disconnected" | "connecting" | "connected";

/** La conexión de WhatsApp por código QR (uazapi) de un negocio, tal como la muestra el panel: nunca trae el token. */
export interface WhatsAppChannel {
  configured: boolean;
  provider: string | null;
  serverUrl: string | null;
  status: WhatsAppStatus;
  /** Los últimos caracteres del token guardado, para reconocerlo. */
  tokenHint: string | null;
  /** Si se guardó el token de administrador del servidor (con él se vuelve a crear la instancia si el servidor la borra). */
  hasAdminToken: boolean;
  phone: string | null;
  profileName: string | null;
  /** Si los mensajes pueden llegar al asistente (el motor tiene una dirección pública para el webhook). */
  webhookReady: boolean;
  /** El código QR para escanear (imagen en `data:`), solo mientras se conecta. */
  qrcode: string | null;
  paircode: string | null;
}
