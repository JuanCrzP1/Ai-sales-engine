import { createContext } from "react";
import type { ProfileUpdate, Session, SignInInput, SignUpInput, UserProfile } from "../../domain/auth/types";

export interface AuthContextValue {
  session: Session | null;
  /** Si el servicio activo comprueba credenciales; si no, la interfaz lo avisa y no pide contraseña. */
  verifiesCredentials: boolean;
  signIn: (input: SignInInput) => Promise<void>;
  signUp: (input: SignUpInput) => Promise<void>;
  signOut: () => Promise<void>;
  updateProfile: (update: ProfileUpdate) => Promise<UserProfile>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
