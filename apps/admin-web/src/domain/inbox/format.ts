import { CHANNEL_LABELS, type ConversationSummary } from "./types";

/** Cómo se nombra al contacto: su nombre o, si el canal no lo da, el canal. */
export function contactLabel(conversation: Pick<ConversationSummary, "contactName" | "channel">): string {
  return conversation.contactName?.trim() || `Cliente de ${CHANNEL_LABELS[conversation.channel]}`;
}

export function initials(text: string): string {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const letters = words.length > 1 ? `${words[0]?.[0] ?? ""}${words[1]?.[0] ?? ""}` : (words[0] ?? "").slice(0, 2);
  return letters.toUpperCase() || "?";
}

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/** "ahora", "hace 5 min", "hace 3 h", "ayer" o la fecha corta. */
export function relativeTime(iso: string, now: Date = new Date()): string {
  const then = new Date(iso);
  const elapsed = now.getTime() - then.getTime();
  if (elapsed < MINUTE) return "ahora";
  if (elapsed < HOUR) return `hace ${Math.floor(elapsed / MINUTE)} min`;
  if (elapsed < DAY && then.getDate() === now.getDate()) return `hace ${Math.floor(elapsed / HOUR)} h`;
  if (elapsed < 2 * DAY) return "ayer";
  return then.toLocaleDateString("es-CO", { day: "numeric", month: "short" });
}

/** Hora del mensaje, como en las apps de chat. */
export function messageTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-CO", { hour: "numeric", minute: "2-digit" });
}

export function fullDate(iso: string): string {
  return new Date(iso).toLocaleString("es-CO", { day: "numeric", month: "long", year: "numeric", hour: "numeric", minute: "2-digit" });
}
