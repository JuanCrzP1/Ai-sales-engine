/**
 * El seguimiento a un cliente que dejó de responder (Mensajes → Seguimiento), como lo valida el motor
 * (`project/app/domain/business_config/contract/assistant.py`, `FollowUp`): hasta 5 mensajes, cada uno después del anterior, el
 * primero como pronto media hora después del último mensaje del cliente y el último como mucho a los 30 días.
 *
 * Viene armado: al encenderlo sin mensajes, el panel pone los recomendados con el trato y los emojis del negocio, y el dueño solo los
 * ajusta si quiere.
 */
import type { FollowUp, FollowUpStep } from "../../contracts/businessConfig.v1";

export type { FollowUp, FollowUpStep };
import { phraseFor, type Phrase, type PlatformStyle } from "./formality";

export const MAX_FOLLOW_UP_STEPS = 5;
export const MIN_FOLLOW_UP_MINUTES = 30;
export const MAX_FOLLOW_UP_MINUTES = 30 * 24 * 60;

export type TimeUnit = "minutes" | "hours" | "days";
export const UNIT_MINUTES: Record<TimeUnit, number> = { minutes: 1, hours: 60, days: 24 * 60 };
export const UNIT_LABELS: Record<TimeUnit, string> = { minutes: "minutos", hours: "horas", days: "días" };

const RECOMMENDED: { afterMinutes: number; text: Phrase }[] = [
  {
    afterMinutes: 60,
    text: {
      tu: "¿Pudiste ver la información? Si te quedó alguna duda, aquí estoy para ayudarte. 😊",
      usted: "¿Pudo ver la información? Si le quedó alguna duda, aquí estoy para ayudarle. 😊",
    },
  },
  {
    afterMinutes: 24 * 60,
    text: {
      tu: "Hola de nuevo 👋 ¿Seguimos con lo que estabas viendo? Cuando quieras te ayudo a terminar.",
      usted: "Hola de nuevo 👋 ¿Seguimos con lo que estaba viendo? Cuando quiera le ayudo a terminar.",
    },
  },
  {
    afterMinutes: 3 * 24 * 60,
    text: {
      tu: "Te escribo por última vez por ahora: si todavía te interesa, respóndeme y lo retomamos.",
      usted: "Le escribo por última vez por ahora: si todavía le interesa, respóndame y lo retomamos.",
    },
  },
];
// Los emojis de los recomendados, con el espacio que los separa: sin ellos si el negocio eligió no usar emojis.
const EMOJIS = [" 😊", " 👋"];

/** Los tres seguimientos recomendados (a la hora, al día siguiente y a los 3 días), con el estilo del negocio. */
export function recommendedFollowUp(style: PlatformStyle = {}): FollowUpStep[] {
  return RECOMMENDED.map(({ afterMinutes, text }) => {
    let message = phraseFor(text, style.formality);
    if (style.emojis === false) for (const emoji of EMOJIS) message = message.replaceAll(emoji, "");
    return { after_minutes: afterMinutes, message };
  });
}

/** El tiempo en la unidad más grande que lo divide exacto: 1440 → 1 día, 90 → 90 minutos. */
export function splitMinutes(minutes: number): { amount: number; unit: TimeUnit } {
  for (const unit of ["days", "hours"] as const) if (minutes > 0 && minutes % UNIT_MINUTES[unit] === 0) return { amount: minutes / UNIT_MINUTES[unit], unit };
  return { amount: minutes, unit: "minutes" };
}

/** «1 hora», «3 días», «45 minutos». */
export function durationText(minutes: number): string {
  const { amount, unit } = splitMinutes(minutes);
  const singular: Record<TimeUnit, string> = { minutes: "minuto", hours: "hora", days: "día" };
  return `${amount} ${amount === 1 ? singular[unit] : UNIT_LABELS[unit]}`;
}

/** El mensaje que se agrega al final: un día después del último, con el texto por escribir. */
export function nextStep(steps: FollowUpStep[]): FollowUpStep {
  const last = steps.at(-1)?.after_minutes ?? 0;
  return { after_minutes: Math.min(MAX_FOLLOW_UP_MINUTES, last + 24 * 60), message: "" };
}

/** Por qué un mensaje de la secuencia no sirve, o null. `index`: su posición. */
export function stepProblem(steps: FollowUpStep[], index: number): string | null {
  const step = steps[index];
  if (!step) return null;
  if (!Number.isFinite(step.after_minutes) || step.after_minutes < MIN_FOLLOW_UP_MINUTES) return "Como pronto, media hora después.";
  if (step.after_minutes > MAX_FOLLOW_UP_MINUTES) return "Como tarde, 30 días después.";
  if (index > 0 && step.after_minutes <= steps[index - 1]!.after_minutes) return "Debe salir después del mensaje anterior.";
  return null;
}

export function isActive(followUp: FollowUp | null | undefined): boolean {
  return Boolean(followUp?.enabled && followUp.steps?.length);
}
