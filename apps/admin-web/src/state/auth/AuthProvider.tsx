import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { authErrorMessage } from "../../domain/auth/messages";
import type { ProfileUpdate, Session, SignInInput, SignUpInput } from "../../domain/auth/types";
import type { AuthService } from "../../repositories/authService";
import { AuthContext, type AuthContextValue } from "./authContext";

type BootState = { status: "loading" } | { status: "error"; message: string } | { status: "ready" };

interface AuthProviderProps {
  service: AuthService;
  children: ReactNode;
  renderLoading: () => ReactNode;
  renderError: (props: { message: string; retry: () => void }) => ReactNode;
}

/** Recupera la sesión al abrir la aplicación y expone las acciones de cuenta. */
export function AuthProvider({ service, children, renderLoading, renderError }: AuthProviderProps) {
  const [boot, setBoot] = useState<BootState>({ status: "loading" });
  const [session, setSession] = useState<Session | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    setBoot({ status: "loading" });
    service.getSession().then(
      (restored) => {
        if (!active) return;
        setSession(restored);
        setBoot({ status: "ready" });
      },
      (error: unknown) => {
        if (active) setBoot({ status: "error", message: authErrorMessage(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [service, attempt]);

  const signIn = useCallback(async (input: SignInInput) => setSession(await service.signIn(input)), [service]);
  const signUp = useCallback(async (input: SignUpInput) => setSession(await service.signUp(input)), [service]);

  const signOut = useCallback(async () => {
    await service.signOut();
    setSession(null);
  }, [service]);

  const updateProfile = useCallback(
    async (update: ProfileUpdate) => {
      const user = await service.updateProfile(update);
      setSession((current) => (current ? { ...current, user } : current));
      return user;
    },
    [service],
  );

  const value = useMemo<AuthContextValue>(
    () => ({ session, verifiesCredentials: service.verifiesCredentials, signIn, signUp, signOut, updateProfile }),
    [session, service.verifiesCredentials, signIn, signUp, signOut, updateProfile],
  );

  if (boot.status === "loading") return <>{renderLoading()}</>;
  if (boot.status === "error") return <>{renderError({ message: boot.message, retry: () => setAttempt((count) => count + 1) })}</>;
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
