/**
 * Lo que la IA entendió de cada mensaje del cliente. Son las cuatro del motor (`project/app/services/ai/output_contract.py`);
 * una prueba del motor comprueba que coinciden.
 */
export const INTENT_LABELS = {
  pain: "Cuenta una necesidad",
  info: "Pide información",
  objection: "Tiene una duda u objeción",
  buy: "Quiere comprar",
} as const;

export type Intent = keyof typeof INTENT_LABELS;

/** En palabras del negocio, o null si la IA no la indicó (nunca se inventa). */
export function intentLabel(intent: string | null | undefined): string | null {
  return intent && intent in INTENT_LABELS ? INTENT_LABELS[intent as Intent] : null;
}
