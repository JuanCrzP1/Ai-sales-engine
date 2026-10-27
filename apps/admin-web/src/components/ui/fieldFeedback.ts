/**
 * Mensaje que acompaña a un control. Es un tipo propio de la interfaz: cualquier
 * objeto con esta forma sirve (por ejemplo, una incidencia de validación del dominio).
 */
export interface FieldFeedback {
  severity: "error" | "warning";
  message: string;
}
