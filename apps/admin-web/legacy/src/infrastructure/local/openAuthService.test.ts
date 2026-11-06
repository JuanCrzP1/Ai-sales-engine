import { AuthError } from "../../domain/auth/types";
import { failingStorage } from "../../test/fakes";
import { createOpenAuthService, nameFromEmail, OPEN_ACCOUNTS_KEY } from "./openAuthService";

const service = () => createOpenAuthService({ storage: window.localStorage });

async function expectAuthError(promise: Promise<unknown>, code: AuthError["code"]) {
  const error = await promise.then(
    () => null,
    (caught: unknown) => caught,
  );
  expect(error).toBeInstanceOf(AuthError);
  expect((error as AuthError).code).toBe(code);
}

describe("createOpenAuthService", () => {
  it("declara que no verifica credenciales", () => {
    expect(service().verifiesCredentials).toBe(false);
  });

  it("entra con cualquier correo y crea la cuenta sin guardar contraseña", async () => {
    const session = await service().signIn({ email: "  Laura.Gomez@Empresa.com ", password: "no-se-usa" });
    expect(session.user).toMatchObject({ name: "Laura Gomez", email: "laura.gomez@empresa.com", avatarUrl: null });
    expect((await service().getSession())?.user.id).toBe(session.user.id);
    expect(window.localStorage.getItem(OPEN_ACCOUNTS_KEY)).not.toContain("no-se-usa");
  });

  it("reutiliza la cuenta del mismo correo", async () => {
    const first = await service().signIn({ email: "a@b.co" });
    await service().signOut();
    expect(await service().getSession()).toBeNull();
    const second = await service().signIn({ email: "A@B.co" });
    expect(second.user.id).toBe(first.user.id);
  });

  it("crear cuenta con un correo existente abre esa cuenta sin cambiarle el nombre", async () => {
    const first = await service().signUp({ name: "Laura", email: "a@b.co" });
    const again = await service().signUp({ name: "Otro", email: "a@b.co" });
    expect(again.user).toMatchObject({ id: first.user.id, name: "Laura" });
  });

  it("actualiza el perfil de la sesión activa y exige sesión", async () => {
    await expectAuthError(service().updateProfile({ name: "X" }), "not_signed_in");
    await service().signIn({ email: "a@b.co" });
    await service().updateProfile({ name: " Nuevo ", avatarUrl: "data:image/jpeg;base64,AAA" });
    expect((await service().getSession())?.user).toMatchObject({ name: "Nuevo", avatarUrl: "data:image/jpeg;base64,AAA" });
  });

  it("informa cuentas guardadas dañadas en vez de descartarlas", async () => {
    window.localStorage.setItem(OPEN_ACCOUNTS_KEY, JSON.stringify([{ id: 1 }]));
    await expectAuthError(service().signIn({ email: "a@b.co" }), "storage_corrupted");
    expect(window.localStorage.getItem(OPEN_ACCOUNTS_KEY)).toBe(JSON.stringify([{ id: 1 }]));
  });

  it("informa cuando el almacenamiento no está disponible", async () => {
    const blocked = createOpenAuthService({ storage: failingStorage("blocked") });
    await expectAuthError(blocked.signIn({ email: "a@b.co" }), "storage_unavailable");
  });

  it("deriva un nombre legible del correo", () => {
    expect(nameFromEmail("ana_maria-ruiz@x.co")).toBe("Ana Maria Ruiz");
    expect(nameFromEmail("@x.co")).toBe("Usuario");
  });
});
