/**
 * El estilo del negocio (trato y emojis) en los textos que escribe la plataforma, como en el motor
 * (`project/app/domain/business_config/formality.py`). Solo «formal» los cambia; con tú, neutral o sin elegir, sale el de siempre
 * (de tú). Las vistas previas los muestran como le llegan al cliente. Lo que escribe el negocio sale tal cual.
 */
import type { ResponseStyle } from "../../contracts/businessConfig.v1";

/** El estilo que cambia los textos de la plataforma: el trato y si el negocio usa emojis (`false`: no los quiere). */
export type PlatformStyle = Pick<ResponseStyle, "formality" | "emojis">;

export type Formality = ResponseStyle["formality"] | "" | undefined;

/** Un texto fijo para el cliente, de tú y de usted. */
export interface Phrase {
  readonly tu: string;
  readonly usted: string;
}

export function phraseFor(phrase: Phrase, formality: Formality): string {
  return formality === "formal" ? phrase.usted : phrase.tu;
}
