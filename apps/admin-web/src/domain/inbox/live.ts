import type { ChatMessage, DeliveryStatus } from "./types";

/**
 * La bandeja en vivo, como Auream: el panel pregunta qué cambió, más seguido cuando hay movimiento y menos en calma, y nada con la
 * pestaña oculta. Los tiempos se pueden cambiar (las pruebas los acortan).
 */
export const liveTiming = {
  /** Con movimiento: durante este tiempo después de cualquier cambio se pregunta cada `activeMs`. */
  activeMs: 1500,
  activeWindowMs: 60_000,
  /** En calma. */
  calmMs: 4000,
  /** La lista de conversaciones (nuevos chats, últimos mensajes, no leídos). */
  listMs: 5000,
};

/** Cada cuánto preguntar, según hace cuánto hubo el último cambio. */
export function pollDelay(lastChangeAt: number, now: number): number {
  return now - lastChangeAt < liveTiming.activeWindowMs ? liveTiming.activeMs : liveTiming.calmMs;
}

/** Une lo que llegó con lo que ya se ve: los mensajes nuevos entran en su lugar y los que cambiaron (sus chulos) se reemplazan. */
export function mergeMessages(current: ChatMessage[], changes: ChatMessage[]): ChatMessage[] {
  if (changes.length === 0) return current;
  const byId = new Map(current.map((message) => [message.id, message]));
  for (const message of changes) byId.set(message.id, message);
  return [...byId.values()].sort((a, b) => a.createdAt.localeCompare(b.createdAt) || a.id.localeCompare(b.id));
}

/** Si algo de lo que llegó es distinto de lo que ya se ve (para saber si hubo movimiento). */
export function hasNews(current: ChatMessage[], changes: ChatMessage[]): boolean {
  const byId = new Map(current.map((message) => [message.id, message]));
  return changes.some((message) => {
    const seen = byId.get(message.id);
    return !seen || seen.status !== message.status || seen.mediaNote !== message.mediaNote || seen.media?.id !== message.media?.id;
  });
}

export const DELIVERY_LABELS: Record<DeliveryStatus, string> = {
  received: "Recibido",
  sending: "Enviando",
  sent: "Enviado",
  delivered: "Entregado",
  read: "Leído",
  failed: "No se envió",
};

/** El tamaño de un archivo, para leerlo de un vistazo. */
export function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} MB`;
}
