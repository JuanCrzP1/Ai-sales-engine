import { createContext } from "react";
import type { PasswordChange, ProfileUpdate, Session, SignInInput, SignUpInput, UserProfile } from "../../domain/auth/types";

export interface AuthContextValue {
  session: Session | null;
  /** Si el servicio activo comprueba credenciales; si no, la interfaz lo avisa y no pide contraseña. */
  verifiesCredentials: boolean;
  signIn: (input: SignInInput) => Promise<void>;
  signUp: (input: SignUpInput) => Promise<void>;
  signOut: () => Promise<void>;
  updateProfile: (update: ProfileUpdate) => Promise<UserProfile>;
  changePassword: (change: PasswordChange) => Promise<void>;
  signOutOtherDevices: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
