import type { AttentionSettings, AttentionView } from "../domain/attention/types";

export type { AttentionSettings, AttentionView, HoursMode, HoursRange, Weekday } from "../domain/attention/types";

/** La atención humana de un negocio. Los fallos se rechazan con `PersistenceError`, con un mensaje y los problemas por campo. */
export interface Attention {
  get(): Promise<AttentionView>;
  save(settings: AttentionSettings): Promise<AttentionView>;
  /** Envía un correo de prueba adonde llegarían los avisos y dice a quién. */
  sendTestEmail(): Promise<string[]>;
}

/** Si este navegador puede recibir notificaciones: sí, no, o solo si se instala el panel (iPhone y iPad). */
export type PushSupport = "supported" | "unsupported" | "install";
export type PushPermission = "default" | "granted" | "denied";

/**
 * Las notificaciones en este navegador o celular: el permiso del navegador, su suscripción y la del servidor. Cada persona las activa
 * en cada dispositivo donde usa el panel.
 */
export interface DevicePush {
  support(): PushSupport;
  permission(): PushPermission;
  /** Si este navegador ya las tiene activadas (y el servidor lo sabe). */
  subscribed(): Promise<boolean>;
  /** Pide el permiso (debe llamarse al tocar un botón) y activa las notificaciones. */
  enable(): Promise<void>;
  disable(): Promise<void>;
  /** Una notificación de prueba a este navegador. */
  test(): Promise<void>;
}
