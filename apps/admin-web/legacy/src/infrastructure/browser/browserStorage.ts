import { PersistenceError } from "../../repositories/persistenceError";

/**
 * Acceso al localStorage del navegador. Nunca oculta un fallo: los errores se
 * convierten en `PersistenceError` para que quien llama pueda informarlos.
 */

/** El localStorage del navegador, o null si no existe o está bloqueado. */
export function safeLocalStorage(): Storage | null {
  try {
    return typeof window !== "undefined" ? window.localStorage : null;
  } catch {
    return null;
  }
}

/** `null` significa que no hay almacenamiento disponible: toda operación se rechaza. */
export type MaybeStorage = Storage | null;

function requireStorage(storage: MaybeStorage): Storage {
  if (!storage) throw new PersistenceError("unavailable");
  return storage;
}

/** El valor guardado, `undefined` si la clave no existe. Rechaza datos que no son JSON. */
export function readJson(storage: MaybeStorage, key: string): unknown {
  let raw: string | null;
  try {
    raw = requireStorage(storage).getItem(key);
  } catch (error) {
    throw error instanceof PersistenceError ? error : new PersistenceError("unavailable", { cause: error });
  }
  if (raw === null) return undefined;
  try {
    return JSON.parse(raw) as unknown;
  } catch (error) {
    throw new PersistenceError("corrupted", { cause: error });
  }
}

export function writeJson(storage: MaybeStorage, key: string, value: unknown): void {
  const target = requireStorage(storage);
  try {
    target.setItem(key, JSON.stringify(value));
  } catch (error) {
    throw new PersistenceError(isQuotaError(error) ? "quota_exceeded" : "unavailable", { cause: error });
  }
}

export function removeKey(storage: MaybeStorage, key: string): void {
  try {
    requireStorage(storage).removeItem(key);
  } catch (error) {
    throw error instanceof PersistenceError ? error : new PersistenceError("unavailable", { cause: error });
  }
}

function isQuotaError(error: unknown): boolean {
  return error instanceof DOMException && (error.name === "QuotaExceededError" || error.name === "NS_ERROR_DOM_QUOTA_REACHED");
}
