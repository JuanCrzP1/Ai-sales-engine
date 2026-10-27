/** Modelo de cuentas y sesión del panel, independiente de dónde se guarden. */

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  /** Foto de perfil como URL (data URL en la implementación local), o null. */
  avatarUrl: string | null;
  createdAt: string;
}

export interface Session {
  user: UserProfile;
  startedAt: string;
}

/** `password` solo es obligatoria para servicios que verifican credenciales. */
export interface SignInInput {
  email: string;
  password?: string;
}

export interface SignUpInput {
  name: string;
  email: string;
  password?: string;
}

export type ProfileUpdate = Partial<Pick<UserProfile, "name" | "avatarUrl">>;

export type AuthErrorCode =
  | "invalid_credentials"
  | "email_taken"
  | "not_signed_in"
  | "storage_unavailable"
  | "storage_corrupted"
  | "unexpected";

export class AuthError extends Error {
  readonly code: AuthErrorCode;

  constructor(code: AuthErrorCode) {
    super(code);
    this.name = "AuthError";
    this.code = code;
  }
}
