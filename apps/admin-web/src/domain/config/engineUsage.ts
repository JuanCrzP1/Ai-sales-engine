import type { SalesMode } from "./types";

/**
 * Qué datos del formulario usa hoy el motor de ventas, según la auditoría de YAML.
 *
 * - "assistant": llega a la IA o al motor y cambia cómo responde.
 * - "stored": se guarda con la configuración, pero el asistente actual todavía no lo usa.
 *
 * Esta es la única fuente de verdad para los avisos de la interfaz.
 */
export type EngineUsage = "assistant" | "stored";

export type ConfigField =
  | "business.name"
  | "business.businessType"
  | "business.description"
  | "business.valueProposition"
  | "offering.name"
  | "offering.description"
  | "offering.category"
  | "offering.price"
  | "offering.features"
  | "behavior.tone"
  | "behavior.salesRules"
  | "behavior.discoveryQuestions"
  | "behavior.recommendationNotes";

const STORED_ALWAYS: ReadonlySet<ConfigField> = new Set<ConfigField>([
  "business.name",
  "business.description",
  "offering.description",
  "behavior.tone",
  "behavior.salesRules",
  "behavior.discoveryQuestions",
  "behavior.recommendationNotes",
]);

/** En catálogo, el asistente actual solo recibe los nombres de las categorías. */
const STORED_IN_CATALOG: ReadonlySet<ConfigField> = new Set<ConfigField>([
  "offering.name",
  "offering.price",
  "offering.features",
]);

export function engineUsage(field: ConfigField, salesMode: SalesMode): EngineUsage {
  if (STORED_ALWAYS.has(field)) return "stored";
  if (salesMode === "catalog" && STORED_IN_CATALOG.has(field)) return "stored";
  return "assistant";
}

export const STORED_FIELD_NOTE =
  "Se guarda con tu configuración. La versión actual del asistente todavía no usa este dato al responder.";

/** Límites de palabras a partir de los cuales el motor recorta el texto. */
export const WORD_LIMITS = {
  businessType: 8,
  valueProposition: 30,
} as const;

/** El motor usa como máximo los dos primeros problemas configurados. */
export const MAX_PROBLEMS_USED = 2;

/** El motor menciona como máximo cuatro categorías del catálogo. */
export const MAX_CATEGORIES_USED = 4;
