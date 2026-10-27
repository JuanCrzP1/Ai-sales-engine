/** Reglas de los formularios de cuenta: única fuente para la interfaz y los servicios. */

export const PASSWORD_MIN_LENGTH = 8;
export const NAME_MAX_LENGTH = 60;

export type AuthField = "name" | "email" | "password" | "confirmPassword";
export type AuthFieldErrors = Partial<Record<AuthField, string>>;

/** Si el servicio de autenticación comprueba contraseñas (ver `AuthService.verifiesCredentials`). */
export interface CredentialPolicy {
  requirePassword: boolean;
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function validateEmail(email: string): string | undefined {
  if (!email.trim()) return "Escribe tu correo electrónico.";
  if (!EMAIL_PATTERN.test(email.trim())) return "Escribe un correo válido, por ejemplo nombre@empresa.com.";
  return undefined;
}

export function validateName(name: string): string | undefined {
  if (!name.trim()) return "Escribe tu nombre.";
  if (name.trim().length > NAME_MAX_LENGTH) return `El nombre puede tener máximo ${NAME_MAX_LENGTH} caracteres.`;
  return undefined;
}

export function validateNewPassword(password: string): string | undefined {
  if (password.length < PASSWORD_MIN_LENGTH) return `La contraseña debe tener al menos ${PASSWORD_MIN_LENGTH} caracteres.`;
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) return "Usa letras y números en la contraseña.";
  return undefined;
}

/**
 * Sin verificación de credenciales basta con escribir un correo (cualquier texto).
 * Con verificación se exigen un correo válido y la contraseña.
 */
export function validateSignIn(input: { email: string; password: string }, policy: CredentialPolicy): AuthFieldErrors {
  if (!policy.requirePassword) {
    return collect({ email: input.email.trim() ? undefined : "Escribe tu correo electrónico." });
  }
  return collect({
    email: validateEmail(input.email),
    password: input.password ? undefined : "Escribe tu contraseña.",
  });
}

export function validateSignUp(
  input: { name: string; email: string; password: string; confirmPassword: string },
  policy: CredentialPolicy,
): AuthFieldErrors {
  const identity = { name: validateName(input.name), email: validateEmail(input.email) };
  if (!policy.requirePassword) return collect(identity);
  return collect({
    ...identity,
    password: validateNewPassword(input.password),
    confirmPassword: input.confirmPassword === input.password ? undefined : "Las contraseñas no coinciden.",
  });
}

export function hasErrors(errors: AuthFieldErrors): boolean {
  return Object.keys(errors).length > 0;
}

/** Conserva solo los campos con mensaje. */
function collect(candidates: AuthFieldErrors): AuthFieldErrors {
  const errors: AuthFieldErrors = {};
  for (const field of ["name", "email", "password", "confirmPassword"] as const) {
    const message = candidates[field];
    if (message) errors[field] = message;
  }
  return errors;
}
