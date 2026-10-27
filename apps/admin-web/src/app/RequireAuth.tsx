import { Navigate, Outlet, useLocation } from "react-router-dom";
import { ACCOUNT_PATHS } from "../navigation/accountPaths";
import { useAuth } from "../state/auth/useAuth";

/** Protege las rutas internas: sin sesión, envía al inicio de sesión y recuerda a dónde se quería ir. */
export function RequireAuth() {
  const { session } = useAuth();
  const location = useLocation();
  if (!session) return <Navigate to={ACCOUNT_PATHS.signIn} replace state={{ from: location.pathname }} />;
  return <Outlet />;
}
