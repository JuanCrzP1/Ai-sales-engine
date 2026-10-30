import { PROMPT_MAX_CATEGORIES, PROMPT_MAX_PROBLEMS, PROMPT_WORD_LIMITS } from "../../contracts/businessConfig.v1";

/**
 * Límites con los que el motor usa los datos del panel. Vienen del contrato generado
 * (`contracts/businessConfig.v1.ts`), que a su vez sale de las políticas del motor: no se copian a mano.
 */

/** Palabras que el asistente usa de cada texto; el resto se corta. */
export const WORD_LIMITS = {
  businessType: PROMPT_WORD_LIMITS.industry,
  valueProposition: PROMPT_WORD_LIMITS.value_proposition,
  description: PROMPT_WORD_LIMITS.description,
  offeringDescription: PROMPT_WORD_LIMITS.offer_description,
} as const;

/** El motor usa como máximo los primeros problemas configurados. */
export const MAX_PROBLEMS_USED = PROMPT_MAX_PROBLEMS;

/** El motor menciona como máximo las primeras categorías del catálogo. */
export const MAX_CATEGORIES_USED = PROMPT_MAX_CATEGORIES;

/** Límites de preguntas frecuentes y del perfil comercial: el motor también los valida. */
export {
  MAX_FAQ_ANSWER_CHARS,
  MAX_FAQ_QUESTION_CHARS,
  MAX_FAQS,
  MAX_PROFILE_ITEM_CHARS,
  MAX_PROFILE_ITEMS,
  MAX_PROMOTIONS,
  MAX_TONE_CHARS,
  RESPONSE_LENGTH_WORD_RANGES,
} from "../../contracts/businessConfig.v1";
