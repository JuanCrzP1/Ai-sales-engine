/** Cómo se lee el consumo de IA de un negocio: cifras cortas y el costo en dólares, que es como cobra OpenRouter. */

const COUNT = new Intl.NumberFormat("es-CO");
const COMPACT = new Intl.NumberFormat("es-CO", { notation: "compact", maximumFractionDigits: 1 });
const DOLLARS = new Intl.NumberFormat("es-CO", { style: "currency", currency: "USD", currencyDisplay: "code", minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function formatCount(value: number): string {
  return COUNT.format(value);
}

/** 1.280 → "1,3 mil"; 2.400.000 → "2,4 M". Debajo de mil, el número completo. */
export function formatTokens(value: number): string {
  return value < 1000 ? COUNT.format(value) : COMPACT.format(value);
}

/** El costo que informó OpenRouter. Null cuando no lo informó: no es lo mismo que cero. */
export function formatCost(value: number | null): string | null {
  if (value === null) return null;
  if (value > 0 && value < 0.01) return `menos de ${DOLLARS.format(0.01)}`;
  return DOLLARS.format(value);
}
