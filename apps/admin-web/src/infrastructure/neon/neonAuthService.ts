import { AuthError, type AuthErrorCode, type Session, type UserProfile } from "../../domain/auth/types";
import type { AuthService } from "../../repositories/authService";

/**
 * Cuentas del panel en la nube con Neon Auth (`@neon/auth`, sobre Better Auth). Las cuentas viven en la base de la plataforma
 * (`neon_auth.user`) y la contraseña solo viaja a Neon Auth. Cada petición a la API lleva el token de la sesión (`token()`):
 * vence a los 15 minutos y el cliente lo renueva solo.
 */

/** Respuesta de cada llamada del cliente de Neon Auth. */
export interface NeonResult<T> {
  data: T | null;
  error: NeonAuthFailure | null;
}

export interface NeonAuthFailure {
  status?: number;
  code?: string;
  message?: string;
}

export interface NeonUser {
  id: string;
  name?: string | null;
  email: string;
  image?: string | null;
  createdAt?: string | Date;
}

export interface NeonSession {
  user: NeonUser;
  session: { token?: string | null; createdAt?: string | Date };
}

/** Lo que el panel usa del cliente de Neon Auth. Se declara aquí para no depender de sus tipos internos y poder probarlo. */
export interface NeonAuthClient {
  getSession(): Promise<NeonResult<NeonSession>>;
  signIn: { email(input: { email: string; password: string }): Promise<NeonResult<unknown>> };
  signUp: { email(input: { email: string; password: string; name: string }): Promise<NeonResult<unknown>> };
  signOut(): Promise<unknown>;
  updateUser(input: { name?: string; image?: string | null }): Promise<NeonResult<unknown>>;
}

/** El servicio de cuentas, más el token de la sesión que piden las peticiones a la API del panel. */
export interface NeonAuthService extends AuthService {
  token(): Promise<string | null>;
}

const iso = (value: string | Date | undefined) => (value ? new Date(value).toISOString() : new Date().toISOString());

function profileOf(user: NeonUser): UserProfile {
  return { id: user.id, name: user.name?.trim() || user.email, email: user.email, avatarUrl: user.image ?? null, createdAt: iso(user.createdAt) };
}

const codeOf = (error: NeonAuthFailure) => `${error.code ?? ""} ${error.message ?? ""}`.toUpperCase();

function signInFailure(error: NeonAuthFailure): AuthErrorCode {
  return error.status === 401 || /INVALID_EMAIL_OR_PASSWORD|INVALID_PASSWORD|USER_NOT_FOUND|CREDENTIAL/.test(codeOf(error)) ? "invalid_credentials" : "unexpected";
}

function signUpFailure(error: NeonAuthFailure): AuthErrorCode {
  return /ALREADY_EXISTS|ALREADY EXISTS/.test(codeOf(error)) ? "email_taken" : "unexpected";
}

/** Un fallo de red o del cliente se informa como error de cuenta, nunca como una excepción sin mensaje. */
async function guarded<T>(call: () => Promise<T>): Promise<T> {
  try {
    return await call();
  } catch (error) {
    if (error instanceof AuthError) throw error;
    throw new AuthError("unexpected");
  }
}

export function createNeonAuthService(client: NeonAuthClient): NeonAuthService {
  const current = async (): Promise<Session | null> => {
    const { data, error } = await client.getSession();
    if (error) throw new AuthError("unexpected");
    if (!data?.session || !data.user) return null;
    return { user: profileOf(data.user), startedAt: iso(data.session.createdAt) };
  };

  const signedIn = async (): Promise<Session> => {
    const session = await current();
    if (!session) throw new AuthError("not_signed_in");
    return session;
  };

  return {
    verifiesCredentials: true,
    getSession: () => guarded(current),
    signIn: ({ email, password }) =>
      guarded(async () => {
        const { error } = await client.signIn.email({ email: email.trim(), password: password ?? "" });
        if (error) throw new AuthError(signInFailure(error));
        return signedIn();
      }),
    signUp: ({ name, email, password }) =>
      guarded(async () => {
        const { error } = await client.signUp.email({ name: name.trim(), email: email.trim(), password: password ?? "" });
        if (error) throw new AuthError(signUpFailure(error));
        return signedIn();
      }),
    signOut: () =>
      guarded(async () => {
        await client.signOut();
      }),
    updateProfile: (update) =>
      guarded(async () => {
        const changes = {
          ...(update.name !== undefined ? { name: update.name.trim() } : {}),
          ...(update.avatarUrl !== undefined ? { image: update.avatarUrl } : {}),
        };
        const { error } = await client.updateUser(changes);
        if (error) throw new AuthError("unexpected");
        return (await signedIn()).user;
      }),
    token: async () => {
      try {
        const { data } = await client.getSession();
        return data?.session?.token ?? null;
      } catch {
        return null;
      }
    },
  };
}
