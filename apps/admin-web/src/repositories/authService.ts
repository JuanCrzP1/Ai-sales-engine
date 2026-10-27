import type { ProfileUpdate, Session, SignInInput, SignUpInput, UserProfile } from "../domain/auth/types";

/**
 * Contrato de autenticación del panel, independiente de dónde vivan las cuentas.
 * Hoy la única implementación es el acceso local abierto (sin servidor); una
 * implementación con servidor cumplirá esta misma interfaz. Los métodos que
 * fallan rechazan con `AuthError`.
 */
export interface AuthService {
  /**
   * Si la implementación comprueba credenciales. Con `false`, la interfaz no pide
   * contraseña y avisa de que el acceso no está verificado.
   */
  readonly verifiesCredentials: boolean;
  /** Sesión activa al abrir la aplicación, o null. */
  getSession(): Promise<Session | null>;
  signIn(input: SignInInput): Promise<Session>;
  signUp(input: SignUpInput): Promise<Session>;
  signOut(): Promise<void>;
  updateProfile(update: ProfileUpdate): Promise<UserProfile>;
}
