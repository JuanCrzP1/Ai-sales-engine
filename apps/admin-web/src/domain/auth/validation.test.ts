import { validateAvatarFile } from "./avatarRules";
import { hasErrors, validateSignIn, validateSignUp } from "./validation";
import { redirectTarget } from "../../navigation/accountPaths";

const OPEN = { requirePassword: false };
const VERIFIED = { requirePassword: true };

describe("validación de cuenta", () => {
  it("sin verificación de credenciales, entrar solo exige escribir el correo", () => {
    expect(validateSignIn({ email: "  ", password: "" }, OPEN)).toEqual({ email: "Escribe tu correo electrónico." });
    expect(hasErrors(validateSignIn({ email: "a@b.co", password: "" }, OPEN))).toBe(false);
    expect(hasErrors(validateSignIn({ email: "cualquier-cosa", password: "" }, OPEN))).toBe(false);
  });

  it("con verificación de credenciales, entrar exige correo válido y contraseña", () => {
    expect(validateSignIn({ email: "", password: "" }, VERIFIED)).toEqual({
      email: "Escribe tu correo electrónico.",
      password: "Escribe tu contraseña.",
    });
    expect(validateSignIn({ email: "no-es-correo", password: "x" }, VERIFIED).email).toMatch(/correo válido/);
    expect(hasErrors(validateSignIn({ email: "a@b.co", password: "x" }, VERIFIED))).toBe(false);
  });

  it("al crear cuenta sin verificación exige nombre y correo válido, sin contraseña", () => {
    expect(Object.keys(validateSignUp({ name: " ", email: "x", password: "", confirmPassword: "" }, OPEN)).sort()).toEqual(["email", "name"]);
    expect(hasErrors(validateSignUp({ name: "Ana", email: "a@b.co", password: "", confirmPassword: "" }, OPEN))).toBe(false);
  });

  it("al crear cuenta con verificación exige contraseña segura y confirmación", () => {
    const errors = validateSignUp({ name: " ", email: "a@b.co", password: "corta", confirmPassword: "otra" }, VERIFIED);
    expect(Object.keys(errors).sort()).toEqual(["confirmPassword", "name", "password"]);
    expect(validateSignUp({ name: "Ana", email: "a@b.co", password: "soloLetras", confirmPassword: "soloLetras" }, VERIFIED).password).toBe(
      "Usa letras y números en la contraseña.",
    );
    expect(hasErrors(validateSignUp({ name: "Ana", email: "a@b.co", password: "clave1234", confirmPassword: "clave1234" }, VERIFIED))).toBe(false);
  });

  it("acepta solo imágenes livianas como foto de perfil", () => {
    expect(validateAvatarFile({ type: "image/png", size: 1000 })).toBeUndefined();
    expect(validateAvatarFile({ type: "application/pdf", size: 1000 })).toMatch(/JPG, PNG/);
    expect(validateAvatarFile({ type: "image/jpeg", size: 6 * 1024 * 1024 })).toMatch(/5 MB/);
  });

  it("solo redirige a rutas internas tras iniciar sesión", () => {
    expect(redirectTarget({ from: "/productos" })).toBe("/productos");
    expect(redirectTarget({ from: "//sitio-externo.com" })).toBe("/");
    expect(redirectTarget({ from: "https://sitio-externo.com" })).toBe("/");
    expect(redirectTarget({ from: "/iniciar-sesion" })).toBe("/");
    expect(redirectTarget(null)).toBe("/");
  });
});
