/** Fallo al leer o guardar datos en el servidor. */

export type PersistenceErrorCode = "unavailable" | "invalid" | "conflict" | "duplicate" | "not_found" | "payment_key" | "ai_key_missing" | "unauthenticated" | "rate_limited" | "unknown";

/** Problema en un campo concreto, con su ruta en el documento (`identity.name`). */
export interface FieldProblem {
  path: string;
  message: string;
}

export class PersistenceError extends Error {
  readonly code: PersistenceErrorCode;
  /** Problemas por campo que señaló el servidor al validar. */
  readonly problems: FieldProblem[];

  constructor(code: PersistenceErrorCode, options?: { cause?: unknown; message?: string; problems?: FieldProblem[] }) {
    super(options?.message ?? code, options);
    this.name = "PersistenceError";
    this.code = code;
    this.problems = options?.problems ?? [];
  }
}

const MESSAGES: Record<PersistenceErrorCode, string> = {
  unavailable: "No se pudo conectar con el servidor. Revisa tu conexión y vuelve a intentarlo.",
  invalid: "Hay datos por corregir.",
  conflict: "Estos datos cambiaron desde que los abriste. Recarga para ver lo último.",
  duplicate: "Ya existe un negocio con ese identificador.",
  not_found: "Ese negocio no existe.",
  payment_key: "Falta la clave de cifrado de los datos de pago en el servidor.",
  ai_key_missing: "Este negocio todavía no tiene su clave de IA. Agrégala en Inteligencia artificial.",
  unauthenticated: "Tu sesión terminó. Vuelve a entrar.",
  rate_limited: "Hiciste muchas solicitudes seguidas. Espera un momento y vuelve a intentarlo.",
  unknown: "No se pudo completar la operación.",
};

/** El mensaje del servidor si lo dio; si no, uno genérico. Nunca incluye los datos enviados. */
export function persistenceErrorMessage(error: unknown): string {
  if (!(error instanceof PersistenceError)) return MESSAGES.unknown;
  return error.message !== error.code ? error.message : MESSAGES[error.code];
}
