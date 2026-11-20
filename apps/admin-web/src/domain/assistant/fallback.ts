/**
 * Lo que envía la plataforma cuando la IA no puede responder y el negocio no escribió su propio mensaje, con el trato del negocio.
 * Es el mismo texto del motor (`project/app/application/pipeline/fallback.py`); una prueba del motor comprueba que coinciden.
 */
import type { Phrase } from "../config/formality";

export const PLATFORM_FALLBACK_REPLY: Phrase = {
  tu: "Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.",
  usted: "Gracias por escribirnos. En este momento no puedo responderle; por favor escríbanos de nuevo en unos minutos.",
};
