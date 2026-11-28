/**
 * La ficha de un cliente: su valor, su responsable, sus notas, sus compras y el historial de lo que le ha pasado, como la arma el
 * servidor (`project/app/domain/business_config/customer_card.py`).
 */
import type { FieldValue } from "./customerFields";
import type { Reminder } from "./reminders";
import { STAGES, STAGE_LABELS, type BoardStage, type Customer, type Sale, type Stage } from "./types";

/** Alguien del equipo que puede ser responsable de un cliente. */
export interface Assignee {
  userId: string;
  email: string | null;
  role: string;
}

export interface CustomerNote {
  id: string;
  body: string;
  author: string | null;
  createdAt: string;
}

/** Un cambio en la ficha: de etapa, de valor o de responsable, y quién lo hizo (el asistente, alguien del equipo o una venta). */
export interface CustomerEvent {
  id: string;
  kind: "stage" | "value" | "owner";
  source: "assistant" | "team" | "sale";
  fromStage: BoardStage | null;
  toStage: BoardStage | null;
  detail: string | null;
  actor: string | null;
  createdAt: string;
}

export interface CustomerCard {
  customer: Customer;
  /** Desde cuándo está en su etapa. */
  stageSince: string | null;
  owner: Assignee | null;
  assignees: Assignee[];
  purchases: Sale[];
  notes: CustomerNote[];
  events: CustomerEvent[];
  /** Sus recordatorios: los pendientes por fecha y los últimos hechos. */
  reminders: Reminder[];
  /** Quien mira, si es del equipo: el responsable que se propone para un recordatorio nuevo. */
  viewerId: string | null;
  /** Todos los campos del negocio con el valor de este cliente, o vacío. */
  fields: FieldValue[];
}

/** Lo que cambia en la ficha: solo lo que viene. `amount` null quita el valor; `ownerId` null deja al cliente sin responsable. */
export interface CardChange {
  amount?: string | null;
  currency?: string;
  ownerId?: string | null;
}

export const MAX_NOTE = 2000;
const ROLE_LABELS: Record<string, string> = { owner: "Dueño", admin: "Administrador", agent: "Asesor" };

export function assigneeLabel(member: Pick<Assignee, "email" | "role">): string {
  const role = ROLE_LABELS[member.role];
  return `${member.email ?? "Alguien del equipo"}${role ? ` · ${role}` : ""}`;
}

/** Las iniciales de un correo o un nombre, para el círculo del responsable: «caro@negocio.com» → «CA». */
export function initialsOf(label: string): string {
  const name = label.split("@")[0]!.replace(/[^\p{L}\p{N}]+/gu, " ").trim();
  const words = name.split(" ").filter(Boolean);
  const letters = words.length > 1 ? `${words[0]![0]}${words[1]![0]}` : name.slice(0, 2);
  return letters.toUpperCase() || "?";
}

/** La etapa que sigue en el embudo, para el botón «Mover a … →»; null si ya es cliente. Quien no compró vuelve a empezar. */
export function nextStage(stage: BoardStage): Stage | null {
  if (stage === "lost") return "new";
  return STAGES[STAGES.indexOf(stage) + 1] ?? null;
}

/** Hace cuánto está en su etapa, a partir de «hace 5 min», «ayer» o «12 nov»: «aquí desde hace 5 min», «aquí desde el 12 nov». */
export function sinceText(relative: string): string {
  if (relative === "ahora") return "acaba de llegar aquí";
  return /^\d/.test(relative) ? `aquí desde el ${relative}` : `aquí desde ${relative}`;
}

/** Cada cambio en una frase: qué pasó y quién lo hizo. `tone`: la etapa a la que llegó, o qué dato cambió (para su color). */
export function describeEvent(event: CustomerEvent): { title: string; by: string; tone: BoardStage | "value" | "owner" } {
  const who = event.actor ? `lo hizo ${event.actor}` : "lo hizo tu equipo";
  if (event.kind === "value") return { title: event.detail ? `Valor: ${event.detail}` : "Se quitó el valor", by: who, tone: "value" };
  if (event.kind === "owner") return { title: event.detail ? `${event.detail} quedó como responsable` : "Quedó sin responsable", by: who, tone: "owner" };
  const stage = event.toStage ?? "new";
  const title = `Pasó a «${STAGE_LABELS[stage]}»${event.detail ? ` · ${event.detail}` : ""}`;
  const by =
    event.source === "assistant"
      ? "lo movió el asistente"
      : event.source === "sale"
        ? event.actor
          ? `por una venta que registró ${event.actor}`
          : "por una venta registrada"
        : who;
  return { title, by, tone: stage };
}
