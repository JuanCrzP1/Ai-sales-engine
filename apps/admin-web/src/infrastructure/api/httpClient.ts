import { PersistenceError, type FieldProblem, type PersistenceErrorCode } from "../../repositories/persistenceError";

/**
 * Acceso a la API local del panel. En desarrollo llega por el proxy de Vite, en el mismo origen. Nunca oculta un fallo:
 * los errores se convierten en `PersistenceError` para que quien llama pueda informarlos.
 */
export interface HttpClient {
  get<T>(path: string): Promise<T>;
  post<T>(path: string, body?: unknown): Promise<T>;
  put<T>(path: string, body: unknown): Promise<T>;
  delete(path: string): Promise<void>;
}

const CODES: Record<string, PersistenceErrorCode> = {
  invalid: "invalid",
  conflict: "conflict",
  duplicate: "duplicate",
  not_found: "not_found",
  payment_key: "payment_key",
};

async function toError(response: Response): Promise<PersistenceError> {
  let payload: { code?: string; message?: string; issues?: FieldProblem[] } = {};
  try {
    payload = (await response.json()) as typeof payload;
  } catch {
    // Sin cuerpo JSON: se usa el mensaje genérico del código.
  }
  // Un 502 o 504 es el proxy de Vite sin servidor detrás.
  const code = (payload.code && CODES[payload.code]) || (response.status >= 502 ? "unavailable" : "unknown");
  return new PersistenceError(code, {
    ...(payload.message ? { message: payload.message } : {}),
    ...(payload.issues ? { problems: payload.issues } : {}),
  });
}

export function createHttpClient(baseUrl = "/api"): HttpClient {
  const request = async <T>(method: string, path: string, body?: unknown): Promise<T> => {
    let response: Response;
    try {
      response = await fetch(`${baseUrl}${path}`, {
        method,
        ...(body !== undefined ? { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {}),
      });
    } catch (error) {
      throw new PersistenceError("unavailable", { cause: error });
    }
    if (!response.ok) throw await toError(response);
    return (response.status === 204 ? undefined : await response.json()) as T;
  };
  return {
    get: (path) => request("GET", path),
    post: (path, body) => request("POST", path, body),
    put: (path, body) => request("PUT", path, body),
    delete: (path) => request<void>("DELETE", path),
  };
}
