/**
 * Los recordatorios del equipo: qué hacer con un cliente y cuándo, como los valida el servidor
 * (`project/app/domain/business_config/reminders.py`). Las fechas viajan en UTC y aquí se muestran en la hora de quien mira.
 */

export interface Reminder {
  id: string;
  conversationId: string;
  customerName: string | null;
  customerContact: string;
  title: string;
  dueAt: string;
  assignee: { userId: string; label: string } | null;
  createdBy: string | null;
  createdAt: string | null;
  doneAt: string | null;
  doneBy: string | null;
}

/** Un recordatorio nuevo. `assigneeId` sin poner: para quien lo crea; null: sin responsable. */
export interface NewReminderInput {
  title: string;
  dueAt: string;
  assigneeId?: string | null;
}

/** El pendiente más próximo de un cliente, para su tarjeta. */
export interface NextReminder {
  title: string;
  dueAt: string;
}

export type ReminderBucket = "overdue" | "today" | "upcoming";
export const MAX_REMINDER_TITLE = 140;

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const TIME = new Intl.DateTimeFormat("es-CO", { hour: "numeric", minute: "2-digit" });
const DATE = new Intl.DateTimeFormat("es-CO", { weekday: "short", day: "numeric", month: "short" });

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

/** «9:00 a. m.», como lo lee alguien en Colombia (sin los espacios raros que pone el navegador). */
function timeOf(date: Date): string {
  return TIME.format(date).replace(/\s/g, " ");
}

export function bucketOf(dueAt: string, now = new Date()): ReminderBucket {
  const due = new Date(dueAt).getTime();
  if (due < now.getTime()) return "overdue";
  return due < startOfDay(now) + DAY ? "today" : "upcoming";
}

/** «hace 5 min», «hace 3 h», «hace 2 días». */
function agoText(elapsed: number): string {
  if (elapsed < HOUR) return `hace ${Math.max(1, Math.floor(elapsed / MINUTE))} min`;
  if (elapsed < DAY) return `hace ${Math.floor(elapsed / HOUR)} h`;
  const days = Math.floor(elapsed / DAY);
  return `hace ${days} ${days === 1 ? "día" : "días"}`;
}

/** Cuándo toca, dicho como lo diría una persona: «Vencido · hace 2 h», «Hoy 3:00 p. m.», «Mañana 9:00 a. m.», «lun 1 dic, 9:00 a. m.». */
export function dueText(dueAt: string, now = new Date()): { text: string; tone: ReminderBucket } {
  const due = new Date(dueAt);
  const tone = bucketOf(dueAt, now);
  if (tone === "overdue") return { text: `Vencido · ${agoText(now.getTime() - due.getTime())}`, tone };
  if (tone === "today") return { text: `Hoy ${timeOf(due)}`, tone };
  if (due.getTime() < startOfDay(now) + 2 * DAY) return { text: `Mañana ${timeOf(due)}`, tone };
  return { text: `${DATE.format(due).replace(/\.$/, "")}, ${timeOf(due)}`, tone };
}

const SHORT_DATE = new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short" });

/** Cuándo toca, corto, para una tarjeta: «Vencido», «Hoy 3:00 p. m.», «Mañana 9:00 a. m.», «3 dic». */
export function dueShort(dueAt: string, now = new Date()): { text: string; tone: ReminderBucket } {
  const due = new Date(dueAt);
  const tone = bucketOf(dueAt, now);
  if (tone === "overdue") return { text: "Vencido", tone };
  if (tone === "today") return { text: `Hoy ${timeOf(due)}`, tone };
  if (due.getTime() < startOfDay(now) + 2 * DAY) return { text: `Mañana ${timeOf(due)}`, tone };
  return { text: SHORT_DATE.format(due).replace(/\.$/, "").replace(" de ", " "), tone };
}

/** Los atajos para un recordatorio nuevo, en la hora de quien mira. */
export function quickDueOptions(now = new Date()): { label: string; at: Date }[] {
  const at = (days: number, hour: number) => new Date(now.getFullYear(), now.getMonth(), now.getDate() + days, hour, 0, 0);
  return [
    { label: "En 1 hora", at: new Date(now.getTime() + HOUR) },
    { label: "Mañana 9:00 a. m.", at: at(1, 9) },
    { label: "En 3 días", at: at(3, 9) },
    { label: "En una semana", at: at(7, 9) },
  ];
}

/** `AAAA-MM-DDTHH:mm` en la hora de quien mira, para un campo de fecha y hora. */
export function localInput(date: Date): string {
  return new Date(date.getTime() - date.getTimezoneOffset() * MINUTE).toISOString().slice(0, 16);
}

/** El valor de un campo de fecha y hora, en UTC para el servidor; null si está vacío o no es una fecha. */
export function fromLocalInput(value: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

/** Los pendientes repartidos por cuándo tocan, cada grupo por fecha. */
export function byBucket(reminders: Reminder[], now = new Date()): Record<ReminderBucket, Reminder[]> {
  const groups: Record<ReminderBucket, Reminder[]> = { overdue: [], today: [], upcoming: [] };
  for (const item of [...reminders].sort((a, b) => a.dueAt.localeCompare(b.dueAt))) groups[bucketOf(item.dueAt, now)].push(item);
  return groups;
}
