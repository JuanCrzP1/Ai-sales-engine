/** Lo que estas reglas necesitan de un modelo de OpenRouter (precios en dólares por millón de tokens). */
export interface PricedModel {
  id: string;
  name: string;
  provider: string;
  promptUsdPerMillion: number;
  completionUsdPerMillion: number;
  free: boolean;
}

/**
 * Cuánto cuesta un modelo en la práctica: lo que gasta una respuesta típica del asistente. Medido en el motor: unos 1.500 tokens
 * de instrucciones y contexto por mensaje, y unos 150 de respuesta.
 */
export const TYPICAL_PROMPT_TOKENS = 1500;
export const TYPICAL_REPLY_TOKENS = 150;

const DOLLARS = new Intl.NumberFormat("es-CO", { style: "currency", currency: "USD", currencyDisplay: "code", minimumFractionDigits: 2, maximumFractionDigits: 2 });
const PRICE = new Intl.NumberFormat("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Dólares por cada 1.000 respuestas típicas. */
export function costPerThousandReplies(model: Pick<PricedModel, "promptUsdPerMillion" | "completionUsdPerMillion">): number {
  return (TYPICAL_PROMPT_TOKENS * model.promptUsdPerMillion + TYPICAL_REPLY_TOKENS * model.completionUsdPerMillion) / 1000;
}

/** "≈ USD 0,32 por cada 1.000 respuestas", "Gratis, con límites de OpenRouter" o "menos de USD 0,01…". */
export function replyCostLabel(model: PricedModel): string {
  if (model.free) return "Gratis, con límites de uso de OpenRouter";
  const cost = costPerThousandReplies(model);
  return cost < 0.01 ? `Menos de ${DOLLARS.format(0.01)} por cada 1.000 respuestas` : `≈ ${DOLLARS.format(cost)} por cada 1.000 respuestas`;
}

/** "Entrada 0,15 · salida 0,60 USD por millón de tokens", como los publica OpenRouter. */
export function tokenPriceLabel(model: PricedModel): string {
  return `Entrada ${PRICE.format(model.promptUsdPerMillion)} · salida ${PRICE.format(model.completionUsdPerMillion)} USD por millón de tokens`;
}

function normalize(text: string): string {
  return text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
}

/** Los modelos cuyo nombre, proveedor o identificador contienen todas las palabras buscadas, sin importar tildes ni mayúsculas. */
export function searchModels<T extends Pick<PricedModel, "id" | "name" | "provider">>(models: T[], query: string): T[] {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  if (words.length === 0) return models;
  return models.filter((model) => {
    const text = normalize(`${model.name} ${model.provider} ${model.id}`);
    return words.every((word) => text.includes(word));
  });
}
