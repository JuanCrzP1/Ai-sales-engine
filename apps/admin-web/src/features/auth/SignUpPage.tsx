import { Link, useLocation } from "react-router-dom";
import { ACCOUNT_PATHS } from "../../navigation/accountPaths";
import { useAuth } from "../../state/auth/useAuth";
import { SignUpForm } from "./SignUpForm";
import { UnverifiedAccessNotice } from "./UnverifiedAccessNotice";

export function SignUpPage() {
  const location = useLocation();
  const { verifiesCredentials } = useAuth();
  return (
    <>
      <header className="auth__header">
        <h1 className="auth__title">Crea tu cuenta</h1>
        <p className="auth__subtitle">Configura tu asistente de ventas en minutos.</p>
      </header>
      {!verifiesCredentials && <UnverifiedAccessNotice />}
      <SignUpForm />
      <p className="auth__switch">
        ¿Ya tienes cuenta?{" "}
        <Link to={ACCOUNT_PATHS.signIn} state={location.state}>
          Iniciar sesión
        </Link>
      </p>
    </>
  );
}
