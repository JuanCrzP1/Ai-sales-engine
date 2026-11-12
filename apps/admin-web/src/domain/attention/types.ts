/**
 * Atención humana (Ajustes → Atención humana): cuándo hay alguien del equipo, qué se le dice al cliente, cuándo retoma la IA un chat
 * que nadie atendió y adónde llegan los avisos. Se aplica al instante: no hay que publicar.
 */

export type Weekday = "lunes" | "martes" | "miercoles" | "jueves" | "viernes" | "sabado" | "domingo";
/** De dónde sale el horario del equipo: el de «Mi negocio», uno propio o siempre hay alguien. */
export type HoursMode = "business" | "custom" | "always";

export const WEEKDAYS: Weekday[] = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"];

export const WEEKDAY_LABELS: Record<Weekday, string> = {
  lunes: "Lunes",
  martes: "Martes",
  miercoles: "Miércoles",
  jueves: "Jueves",
  viernes: "Viernes",
  sabado: "Sábado",
  domingo: "Domingo",
};

export const WEEKDAY_SHORT: Record<Weekday, string> = {
  lunes: "Lun",
  martes: "Mar",
  miercoles: "Mié",
  jueves: "Jue",
  viernes: "Vie",
  sabado: "Sáb",
  domingo: "Dom",
};

export interface HoursRange {
  days: Weekday[];
  /** HH:MM, 24 h. */
  opens: string;
  closes: string;
}

/** Lo que el negocio decide. */
export interface AttentionSettings {
  hoursMode: HoursMode;
  teamHours: HoursRange[];
  timezone: string;
  /** Lo que se le dice al cliente sobre cuánto tarda el equipo (0: no se le dice). */
  replyMinutes: number;
  /** Cuánto espera el cliente antes de que la IA retome el chat (null: nunca). */
  resumeAfterMinutes: number | null;
  emailEnabled: boolean;
  /** Sin correo propio, los avisos llegan al de la cuenta. */
  emailTo: string | null;
}

/** Los ajustes con lo que el panel necesita para mostrarlos con honestidad. */
export interface AttentionView extends AttentionSettings {
  updatedAt: string | null;
  /** El horario de «Mi negocio» (vacío si no tiene). */
  businessHours: HoursRange[];
  /** Adónde llegan los correos si no se escribe otro: el de la cuenta dueña. */
  accountEmails: string[];
  /** La plataforma tiene el correo de avisos activado. */
  emailAvailable: boolean;
  teamAvailableNow: boolean;
  nextOpening: string | null;
  options: {
    timezones: { id: string; label: string }[];
    replyMinutes: number[];
    resumeAfterMinutes: number[];
  };
}

function clock(value: string): string {
  const [hours = 0, minutes = 0] = value.split(":").map(Number);
  if (hours === 12 && minutes === 0) return "12:00 m.";
  return `${hours % 12 || 12}:${String(minutes).padStart(2, "0")} ${hours < 12 ? "a. m." : "p. m."}`;
}

function daysText(days: Weekday[]): string {
  const ordered = WEEKDAYS.filter((day) => days.includes(day));
  const names = ordered.map((day) => WEEKDAY_LABELS[day].toLowerCase());
  if (ordered.length === 7) return "todos los días";
  if (ordered.length === 1) return `el ${names[0]}`;
  const indexes = ordered.map((day) => WEEKDAYS.indexOf(day));
  const consecutive = indexes.every((value, index) => index === 0 || value === indexes[index - 1]! + 1);
  if (ordered.length >= 3 && consecutive) return `de ${names[0]} a ${names[names.length - 1]}`;
  return `${names.slice(0, -1).join(", ")} y ${names[names.length - 1]}`;
}

/** El horario en una frase, como lo dice el asistente: «de lunes a viernes de 8:00 a. m. a 6:00 p. m.». */
export function hoursText(hours: HoursRange[]): string {
  const parts = hours.map((range) => `${daysText(range.days)} de ${clock(range.opens)} a ${clock(range.closes)}`);
  if (parts.length <= 1) return parts[0] ?? "";
  return `${parts.slice(0, -1).join(", ")} y ${parts[parts.length - 1]}`;
}

/** «unos 10 minutos», «una hora», «unas 2 horas». */
export function waitText(minutes: number): string {
  if (minutes < 60) return `unos ${minutes} minutos`;
  if (minutes === 60) return "una hora";
  return minutes % 60 === 0 ? `unas ${minutes / 60} horas` : `unos ${minutes} minutos`;
}

/** Lo que recibe el cliente cuando su chat pasa al equipo dentro del horario (null: no se le dice nada más). */
export function waitNotice(replyMinutes: number): string | null {
  return replyMinutes > 0 ? `Una persona de nuestro equipo te responderá en ${waitText(replyMinutes)}.` : null;
}

/** El horario que usa el equipo según lo elegido (vacío: siempre hay alguien). */
export function effectiveHours(settings: Pick<AttentionSettings, "hoursMode" | "teamHours">, businessHours: HoursRange[]): HoursRange[] {
  if (settings.hoursMode === "always") return [];
  return settings.hoursMode === "custom" ? settings.teamHours : businessHours;
}
