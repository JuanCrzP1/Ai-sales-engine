import type { ApplicationServices } from "../app/compositionRoot";
import { AuthError, type Session, type UserProfile } from "../domain/auth/types";
import { normalizeEmail } from "../domain/auth/validation";
import { createLocalConfigRepository } from "../infrastructure/local/localConfigRepository";
import { createOpenAuthService } from "../infrastructure/local/openAuthService";
import type { AuthService } from "../repositories/authService";
import type { ConfigRepository } from "../repositories/configRepository";
import { PersistenceError } from "../repositories/persistenceError";

export const TEST_ACCOUNT = { name: "Laura Gómez", email: "laura@empresa.com", password: "clave1234" };

/** Servicios como los de la aplicación, sobre el localStorage simulado de jsdom. */
export function createTestServices(
  overrides: Partial<ApplicationServices> = {},
  storage: Storage = window.localStorage,
): ApplicationServices {
  return {
    auth: createOpenAuthService({ storage }),
    createConfigRepository: (accountId) => createLocalConfigRepository(accountId, storage),
    ...overrides,
  };
}

/** Crea la cuenta de prueba y deja la sesión iniciada. */
export async function signedInServices(
  overrides: Partial<ApplicationServices> = {},
): Promise<{ services: ApplicationServices; session: Session }> {
  const services = createTestServices(overrides);
  const session = await services.auth.signUp(TEST_ACCOUNT);
  return { services, session };
}

/**
 * localStorage que falla: "blocked" no permite leer ni escribir (navegador bloqueado),
 * "quota" permite leer pero rechaza escribir como cuando el almacenamiento está lleno.
 */
export function failingStorage(mode: "blocked" | "quota"): Storage {
  const fail = (operation: "read" | "write") => {
    if (mode === "blocked") throw new DOMException("Almacenamiento bloqueado", "SecurityError");
    if (operation === "write") throw new DOMException("Almacenamiento lleno", "QuotaExceededError");
  };
  return {
    length: 0,
    clear: () => fail("write"),
    key: () => null,
    getItem: () => {
      fail("read");
      return null;
    },
    setItem: () => fail("write"),
    removeItem: () => fail("write"),
  };
}

/** Repositorio cuyo guardado falla mientras `failing.current` sea true; la carga funciona. */
export function flakyConfigRepository(inner: ConfigRepository, failing: { current: boolean }): ConfigRepository {
  return {
    load: () => inner.load(),
    save: (config) => (failing.current ? Promise.reject(new PersistenceError("quota_exceeded")) : inner.save(config)),
    clear: () => inner.clear(),
  };
}

/**
 * Servicio en memoria que SÍ verifica credenciales (contraseñas en claro: solo para pruebas).
 * Permite probar la interfaz que tendrá la futura autenticación real en servidor.
 */
export function createVerifyingAuthService(): AuthService {
  const accounts = new Map<string, { profile: UserProfile; password: string }>();
  let session: Session | null = null;
  const start = (profile: UserProfile): Session => (session = { user: profile, startedAt: new Date().toISOString() });

  return {
    verifiesCredentials: true,
    getSession: async () => session,
    async signIn({ email, password }) {
      const account = accounts.get(normalizeEmail(email));
      if (!account || account.password !== password) throw new AuthError("invalid_credentials");
      return start(account.profile);
    },
    async signUp({ name, email, password }) {
      const key = normalizeEmail(email);
      if (accounts.has(key)) throw new AuthError("email_taken");
      const profile: UserProfile = { id: `cuenta_${accounts.size + 1}`, name, email: key, avatarUrl: null, createdAt: new Date().toISOString() };
      accounts.set(key, { profile, password: password ?? "" });
      return start(profile);
    },
    async signOut() {
      session = null;
    },
    async updateProfile(update) {
      if (!session) throw new AuthError("not_signed_in");
      const profile = { ...session.user, ...update };
      const account = accounts.get(profile.email);
      if (account) account.profile = profile;
      session = { ...session, user: profile };
      return profile;
    },
  };
}
