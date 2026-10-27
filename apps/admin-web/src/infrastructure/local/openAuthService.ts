import { AuthError, type ProfileUpdate, type Session, type UserProfile } from "../../domain/auth/types";
import { normalizeEmail } from "../../domain/auth/validation";
import { createId } from "../../lib/ids";
import type { AuthService } from "../../repositories/authService";
import { PersistenceError } from "../../repositories/persistenceError";
import { readJson, removeKey, safeLocalStorage, writeJson, type MaybeStorage } from "../browser/browserStorage";

/**
 * ACCESO LOCAL ABIERTO, SIN VERIFICACIÓN. Mientras no exista un servidor, cualquier
 * correo abre la sesión y, si no existe, se crea la cuenta en este navegador. No se
 * pide ni se guarda contraseña (`verifiesCredentials = false`, y la interfaz lo avisa).
 * No protege datos: es la implementación provisional de `AuthService` hasta tener
 * autenticación real en servidor.
 */

export const OPEN_ACCOUNTS_KEY = "ai-sales-engine.admin-web.open-accounts.v1";
export const OPEN_SESSION_KEY = "ai-sales-engine.admin-web.open-session.v1";

interface StoredSession {
  userId: string;
  startedAt: string;
}

interface OpenAuthOptions {
  /** Por defecto, el localStorage del navegador; `null` simula que no está disponible. */
  storage?: MaybeStorage;
  now?: () => Date;
}

export function createOpenAuthService(options: OpenAuthOptions = {}): AuthService {
  const storage = options.storage === undefined ? safeLocalStorage() : options.storage;
  const now = options.now ?? (() => new Date());

  /** Las cuentas guardadas. Datos con otra forma se informan en vez de descartarse. */
  const loadProfiles = (): UserProfile[] => {
    const value = readJson(storage, OPEN_ACCOUNTS_KEY);
    if (value === undefined) return [];
    if (!Array.isArray(value) || !value.every(isProfile)) throw new PersistenceError("corrupted");
    return value;
  };

  const startSession = (profile: UserProfile): Session => {
    const session: StoredSession = { userId: profile.id, startedAt: now().toISOString() };
    writeJson(storage, OPEN_SESSION_KEY, session);
    return { user: profile, startedAt: session.startedAt };
  };

  const currentSession = (): Session | null => {
    const stored = readJson(storage, OPEN_SESSION_KEY);
    // La sesión es solo un puntero a una cuenta: si no es válida, simplemente no hay sesión.
    if (!isStoredSession(stored)) return null;
    const user = loadProfiles().find((profile) => profile.id === stored.userId);
    return user ? { user, startedAt: stored.startedAt } : null;
  };

  /** La cuenta del correo, creándola si no existe. */
  const openAccount = (email: string, name?: string): UserProfile => {
    const profiles = loadProfiles();
    const normalized = normalizeEmail(email);
    const existing = profiles.find((profile) => profile.email === normalized);
    if (existing) return existing;

    const profile: UserProfile = {
      id: createId("cuenta"),
      name: name?.trim() || nameFromEmail(normalized),
      email: normalized,
      avatarUrl: null,
      createdAt: now().toISOString(),
    };
    writeJson(storage, OPEN_ACCOUNTS_KEY, [...profiles, profile]);
    return profile;
  };

  return {
    verifiesCredentials: false,
    getSession: () => run(currentSession),
    signIn: ({ email }) => run(() => startSession(openAccount(email))),
    signUp: ({ name, email }) => run(() => startSession(openAccount(email, name))),
    signOut: () => run(() => removeKey(storage, OPEN_SESSION_KEY)),
    updateProfile: (update: ProfileUpdate) =>
      run(() => {
        const session = currentSession();
        if (!session) throw new AuthError("not_signed_in");
        const profile: UserProfile = {
          ...session.user,
          ...(update.name !== undefined ? { name: update.name.trim() } : {}),
          ...(update.avatarUrl !== undefined ? { avatarUrl: update.avatarUrl } : {}),
        };
        writeJson(
          storage,
          OPEN_ACCOUNTS_KEY,
          loadProfiles().map((item) => (item.id === profile.id ? profile : item)),
        );
        return profile;
      }),
  };
}

/** Ejecuta una operación y traduce los fallos de almacenamiento al lenguaje de cuentas. */
async function run<T>(operation: () => T): Promise<T> {
  try {
    return operation();
  } catch (error) {
    if (error instanceof PersistenceError) {
      throw new AuthError(error.code === "corrupted" ? "storage_corrupted" : "storage_unavailable");
    }
    throw error;
  }
}

/** "laura.gomez@empresa.com" → "Laura Gomez". */
export function nameFromEmail(email: string): string {
  const words = (email.split("@")[0] ?? "").split(/[._\-+\s]+/).filter(Boolean);
  const name = words.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
  return name || "Usuario";
}

function isProfile(value: unknown): value is UserProfile {
  const candidate = value as Partial<UserProfile> | null;
  return (
    typeof candidate === "object" &&
    candidate !== null &&
    typeof candidate.id === "string" &&
    typeof candidate.email === "string" &&
    typeof candidate.name === "string" &&
    typeof candidate.createdAt === "string" &&
    (candidate.avatarUrl === null || typeof candidate.avatarUrl === "string")
  );
}

function isStoredSession(value: unknown): value is StoredSession {
  const candidate = value as Partial<StoredSession> | null;
  return typeof candidate === "object" && candidate !== null && typeof candidate.userId === "string" && typeof candidate.startedAt === "string";
}
