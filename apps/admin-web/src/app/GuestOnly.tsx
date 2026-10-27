import { Navigate, Outlet, useLocation } from "react-router-dom";
import { redirectTarget } from "../navigation/accountPaths";
import { useAuth } from "../state/auth/useAuth";

/** Pantallas solo para quien no ha iniciado sesión (entrar y crear cuenta). */
export function GuestOnly() {
  const { session } = useAuth();
  const location = useLocation();
  return session ? <Navigate to={redirectTarget(location.state)} replace /> : <Outlet />;
}
