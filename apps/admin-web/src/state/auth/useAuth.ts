import { useContext } from "react";
import type { UserProfile } from "../../domain/auth/types";
import { AuthContext, type AuthContextValue } from "./authContext";

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth debe usarse dentro de <AuthProvider>.");
  return context;
}

/** Usuario de la sesión. Solo para pantallas protegidas (dentro de <RequireAuth>). */
export function useCurrentUser(): UserProfile {
  const { session } = useAuth();
  if (!session) throw new Error("useCurrentUser requiere una sesión activa.");
  return session.user;
}
