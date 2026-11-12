import { describe, expect, it, vi } from "vitest";
import { AuthError } from "../../domain/auth/types";
import { createNeonAuthService, type NeonAuthClient, type NeonResult, type NeonSession } from "./neonAuthService";

const USER = { id: "usuario-1", name: "Ana", email: "ana@example.com", image: null, createdAt: "2026-11-10T00:00:00.000Z" };

/** Neon Auth de mentira: una cuenta con contraseña y una sesión con su token. */
function fakeClient(overrides: Partial<NeonAuthClient> = {}) {
  let session: NeonSession | null = null;
  const ok = <T,>(data: T): NeonResult<T> => ({ data, error: null });
  const client: NeonAuthClient = {
    getSession: vi.fn(async (): Promise<NeonResult<NeonSession>> => ({ data: session, error: null })),
    signIn: {
      email: vi.fn(async ({ email, password }) => {
        if (email !== USER.email || password !== "clave-segura-1") return { data: null, error: { status: 401, code: "INVALID_EMAIL_OR_PASSWORD", message: "Invalid email or password" } };
        session = { user: USER, session: { token: "jwt-de-ana", createdAt: "2026-11-10T01:00:00.000Z" } };
        return ok({});
      }),
    },
    signUp: {
      email: vi.fn(async ({ email }) => {
        if (email === USER.email) return { data: null, error: { status: 422, code: "USER_ALREADY_EXISTS", message: "User already exists" } };
        session = { user: { ...USER, email }, session: { token: "jwt-nuevo" } };
        return ok({});
      }),
    },
    signOut: vi.fn(async () => {
      session = null;
      return ok({});
    }),
    updateUser: vi.fn(async () => ok({})),
    // Como Better Auth: con la contraseña actual equivocada responde 400 INVALID_PASSWORD.
    changePassword: vi.fn(async ({ currentPassword }) =>
      currentPassword === "clave-segura-1" ? ok({}) : { data: null, error: { status: 400, code: "INVALID_PASSWORD", message: "Invalid password" } },
    ),
    revokeOtherSessions: vi.fn(async () => ok({})),
    ...overrides,
  };
  return client;
}

async function authError(promise: Promise<unknown>): Promise<string> {
  try {
    await promise;
  } catch (error) {
    if (error instanceof AuthError) return error.code;
    throw error;
  }
  throw new Error("Debía fallar.");
}

describe("cuentas con Neon Auth", () => {
  it("verifica la contraseña y, al entrar, entrega la sesión y su token para la API", async () => {
    const service = createNeonAuthService(fakeClient());
    expect(service.verifiesCredentials).toBe(true);
    expect(await service.getSession()).toBeNull();
    expect(await service.token()).toBeNull();

    const session = await service.signIn({ email: " ana@example.com ", password: "clave-segura-1" });
    expect(session.user).toEqual({ id: "usuario-1", name: "Ana", email: "ana@example.com", avatarUrl: null, createdAt: "2026-11-10T00:00:00.000Z" });
    expect(session.startedAt).toBe("2026-11-10T01:00:00.000Z");
    expect(await service.token()).toBe("jwt-de-ana");

    await service.signOut();
    expect(await service.getSession()).toBeNull();
    expect(await service.token()).toBeNull();
  });

  it("señala una contraseña equivocada y un correo ya registrado", async () => {
    const service = createNeonAuthService(fakeClient());
    expect(await authError(service.signIn({ email: USER.email, password: "otra-clave-9" }))).toBe("invalid_credentials");
    expect(await authError(service.signUp({ name: "Ana", email: USER.email, password: "clave-segura-1" }))).toBe("email_taken");
  });

  it("crear una cuenta deja la sesión abierta", async () => {
    const client = fakeClient();
    const service = createNeonAuthService(client);
    const session = await service.signUp({ name: " Beto ", email: "beto@example.com", password: "clave-segura-2" });
    expect(client.signUp.email).toHaveBeenCalledWith({ name: "Beto", email: "beto@example.com", password: "clave-segura-2" });
    expect(session.user.email).toBe("beto@example.com");
    expect(await service.token()).toBe("jwt-nuevo");
  });

  it("cambia la contraseña pidiendo la actual y puede cerrar la sesión en los demás equipos", async () => {
    const client = fakeClient();
    const auth = createNeonAuthService(client);
    await auth.signIn({ email: USER.email, password: "clave-segura-1" });
    expect(await authError(auth.changePassword({ currentPassword: "equivocada", newPassword: "nueva-clave-2", signOutOtherDevices: true }))).toBe("wrong_password");
    await auth.changePassword({ currentPassword: "clave-segura-1", newPassword: "nueva-clave-2", signOutOtherDevices: true });
    expect(client.changePassword).toHaveBeenLastCalledWith({ currentPassword: "clave-segura-1", newPassword: "nueva-clave-2", revokeOtherSessions: true });
    await auth.signOutOtherDevices();
    expect(client.revokeOtherSessions).toHaveBeenCalledTimes(1);
  });

  it("una caída de la red se informa como error de cuenta y el token queda vacío", async () => {
    const down = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });
    const service = createNeonAuthService(fakeClient({ getSession: down }));
    expect(await authError(service.getSession())).toBe("unexpected");
    expect(await service.token()).toBeNull();
  });
});
