/** Fallo al leer o guardar datos, sea cual sea el almacenamiento (navegador hoy, API mañana). */

export type PersistenceErrorCode = "unavailable" | "quota_exceeded" | "corrupted" | "unknown";

export class PersistenceError extends Error {
  readonly code: PersistenceErrorCode;

  constructor(code: PersistenceErrorCode, options?: { cause?: unknown }) {
    super(code, options);
    this.name = "PersistenceError";
    this.code = code;
  }
}

const MESSAGES: Record<PersistenceErrorCode, string> = {
  unavailable: "El almacenamiento de este navegador no está disponible (por ejemplo, en modo privado o bloqueado).",
  quota_exceeded: "El almacenamiento de este navegador está lleno.",
  corrupted: "Los datos guardados están dañados y no se pueden leer.",
  unknown: "No se pudo acceder a los datos guardados.",
};

export function persistenceErrorMessage(error: unknown): string {
  return MESSAGES[error instanceof PersistenceError ? error.code : "unknown"];
}
