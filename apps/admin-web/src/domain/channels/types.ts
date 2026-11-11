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
