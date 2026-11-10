import {
  MAX_CATEGORIES,
  MAX_CUSTOMER_PROBLEMS,
  MAX_DESCRIPTION_CHARS,
  MAX_INDUSTRY_CHARS,
  MAX_OFFER_DESCRIPTION_CHARS,
  MAX_VALUE_PROPOSITION_CHARS,
} from "../../contracts/businessConfig.v1";

/**
 * Límites con los que el motor usa los datos del panel. Vienen del contrato generado
 * (`contracts/businessConfig.v1.ts`), que a su vez sale de las políticas del motor: no se copian a mano.
 */

/** Largo máximo de cada texto, en caracteres. El asistente lo usa completo; el campo no deja escribir más. */
export const TEXT_LIMITS = {
  businessType: MAX_INDUSTRY_CHARS,
  description: MAX_DESCRIPTION_CHARS,
  valueProposition: MAX_VALUE_PROPOSITION_CHARS,
  offeringDescription: MAX_OFFER_DESCRIPTION_CHARS,
} as const;

/** Cuántas categorías y problemas del cliente admite el negocio. El asistente los usa todos. */
export { MAX_CATEGORIES, MAX_CUSTOMER_PROBLEMS };

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
