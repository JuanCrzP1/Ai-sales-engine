/**
 * El mensaje con los datos de pago, como lo arma el servidor (`project/app/domain/business_config/payment_message.py`): una
 * plantilla con `{medio}`, `{datos}` (obligatorio), `{titular}` e `{instrucciones}`. Una línea con un marcador vacío no sale. Aquí sirve para avisar
 * mientras se escribe y para la vista previa; quien manda es el servidor.
 */
export const PAYMENT_PLACEHOLDERS = ["medio", "datos", "titular", "instrucciones"] as const;

export const DEFAULT_PAYMENT_DETAILS =
  "💳 *Datos para pagar*\n\n*{medio}*\n{datos}\nA nombre de: {titular}\n{instrucciones}\n\nCuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅";

const PLACEHOLDER = /\{([^{}]*)\}/g;

/** Cómo se nombra cada tipo de cuenta en el mensaje (igual que el servidor). */
export const ACCOUNT_TYPE_TEXT: Record<string, string> = { ahorros: "Cuenta de ahorros", corriente: "Cuenta corriente" };

/** Por qué la plantilla no sirve, o null. */
export function paymentTemplateProblem(template: string): string | null {
  const names = [...template.matchAll(PLACEHOLDER)].map((match) => match[1] ?? "");
  const unknown = names.find((name) => !(PAYMENT_PLACEHOLDERS as readonly string[]).includes(name));
  if (unknown !== undefined) return `La plantilla tiene un marcador que no existe: {${unknown}}. Usa {medio}, {datos}, {titular} o {instrucciones}.`;
  if (!names.includes("datos")) return "La plantilla debe tener {datos}: ahí van el número, la cuenta o el enlace para pagar.";
  return null;
}

/** El mensaje que recibe el cliente. Sin plantilla propia (o con una que no sirve), la de la plataforma. */
export function renderPaymentDetails(template: string | null | undefined, values: { medio: string; datos: string; titular?: string; instrucciones?: string }): string {
  const chosen = template && template.trim() && paymentTemplateProblem(template) === null ? template : DEFAULT_PAYMENT_DETAILS;
  const filled: Record<string, string> = {
    medio: values.medio.trim(),
    datos: values.datos.trim(),
    titular: (values.titular ?? "").trim(),
    instrucciones: (values.instrucciones ?? "").trim(),
  };
  const lines = chosen
    .trim()
    .split("\n")
    .filter((line) => [...line.matchAll(PLACEHOLDER)].every((match) => Boolean(filled[match[1] ?? ""])))
    .map((line) => line.replace(PLACEHOLDER, (_whole, name: string) => filled[name] ?? "").trimEnd());
  const message = lines.join("\n").replace(/\n{3,}/g, "\n\n").trim();
  // Si la plantilla del negocio no tiene {instrucciones} y el medio tiene una, va al final: el cliente nunca se queda sin ella.
  return filled.instrucciones && !chosen.includes("{instrucciones}") ? `${message}\n\n${filled.instrucciones}` : message;
}
