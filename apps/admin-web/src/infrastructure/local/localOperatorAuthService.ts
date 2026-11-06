import type { Session, UserProfile } from "../../domain/auth/types";
import type { AuthService } from "../../repositories/authService";

/**
 * Sin autenticación: en esta fase el panel y su API solo funcionan en este equipo y quien lo usa es quien administra.
 * La autenticación definitiva llega con la fase de nube; bastará con otra implementación de este mismo contrato.
 * Nada se guarda en el navegador.
 */
const OPERATOR: UserProfile = {
  id: "operador-local",
  name: "Administración local",
  email: "",
  avatarUrl: null,
  createdAt: new Date(0).toISOString(),
};

function unsupported(): Promise<never> {
  return Promise.reject(new Error("La autenticación todavía no está disponible."));
}

export function createLocalOperatorAuthService(): AuthService {
  const session: Session = { user: OPERATOR, startedAt: new Date().toISOString() };
  return {
    verifiesCredentials: false,
    getSession: async () => session,
    signIn: unsupported,
    signUp: unsupported,
    signOut: unsupported,
    updateProfile: unsupported,
  };
}
