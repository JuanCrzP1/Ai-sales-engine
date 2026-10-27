import { Link, useLocation } from "react-router-dom";
import { ACCOUNT_PATHS } from "../../navigation/accountPaths";
import { useAuth } from "../../state/auth/useAuth";
import { SignInForm } from "./SignInForm";
import { UnverifiedAccessNotice } from "./UnverifiedAccessNotice";

export function SignInPage() {
  const location = useLocation();
  const { verifiesCredentials } = useAuth();
  return (
    <>
      <header className="auth__header">
        <h1 className="auth__title">Bienvenido de nuevo</h1>
        <p className="auth__subtitle">Entra para configurar tu asistente de ventas.</p>
      </header>
      {!verifiesCredentials && <UnverifiedAccessNotice />}
      <SignInForm />
      <p className="auth__switch">
        ¿No tienes cuenta?{" "}
        <Link to={ACCOUNT_PATHS.signUp} state={location.state}>
          Crear cuenta
        </Link>
      </p>
    </>
  );
}
