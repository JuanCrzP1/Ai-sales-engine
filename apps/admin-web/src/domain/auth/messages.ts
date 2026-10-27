import { AuthError, type AuthErrorCode } from "./types";

const MESSAGES: Record<AuthErrorCode, string> = {
  invalid_credentials: "El correo o la contraseña no son correctos.",
  email_taken: "Ya existe una cuenta con ese correo. Inicia sesión.",
  not_signed_in: "Tu sesión terminó. Vuelve a iniciar sesión.",
  storage_unavailable: "No se pudo guardar la información en este navegador. Revisa que el almacenamiento esté permitido.",
  storage_corrupted: "Los datos de cuentas guardados en este navegador están dañados y no se pueden leer.",
  unexpected: "Algo salió mal. Inténtalo de nuevo.",
};

/** Mensaje para el usuario a partir de cualquier error de cuenta. */
export function authErrorMessage(error: unknown): string {
  return MESSAGES[error instanceof AuthError ? error.code : "unexpected"];
}
