import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, LinkButton } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { ROLE_DESCRIPTIONS, ROLE_LABELS, expiryText, invitationPath } from "../../domain/team/team";
import { ACCOUNT_PATHS } from "../../navigation/accountPaths";
import { workspacePath } from "../../navigation/navItems";
import { persistenceErrorMessage } from "../../state/directoryContext";
import { useAuth } from "../../state/auth/useAuth";
import { useInvitation } from "../../state/useTeam";

/**
 * Lo que ve quien abre un enlace de invitación: a qué negocio lo invitan, con qué rol y quién. Sin sesión, crea su cuenta o entra
 * (y vuelve aquí); con sesión, acepta con la cuenta del correo invitado y queda dentro del negocio.
 */
export function InvitationPage() {
  const { token = "" } = useParams();
  const { state, accept } = useInvitation(token);
  const { session, verifiesCredentials, signOut } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const here = invitationPath(token);

  if (state.status === "loading") return <p className="auth__subtitle">Revisando la invitación…</p>;
  if (state.status === "error") {
    return (
      <div className="auth__form">
        <header className="auth__header">
          <h1 className="auth__title">Esta invitación no sirve</h1>
          <p className="auth__subtitle">{state.message}</p>
        </header>
        <LinkButton to="/">Ir al panel</LinkButton>
      </div>
    );
  }

  const { invitation } = state;
  const signedAs = verifiesCredentials ? session?.user.email ?? null : null;
  const otherAccount = signedAs !== null && signedAs.trim().toLowerCase() !== invitation.email;

  const join = async () => {
    setBusy(true);
    setProblem(null);
    try {
      const business = await accept();
      navigate(workspacePath(business), { replace: true });
    } catch (reason) {
      setProblem(persistenceErrorMessage(reason));
      setBusy(false);
    }
  };

  return (
    <div className="auth__form">
      <header className="auth__header">
        <p className="invitation__eyebrow">Invitación al equipo</p>
        <h1 className="auth__title">Únete a {invitation.businessName}</h1>
        <p className="auth__subtitle">
          {invitation.invitedBy} te invitó como <strong>{ROLE_LABELS[invitation.role]}</strong>. {ROLE_DESCRIPTIONS[invitation.role]}
        </p>
      </header>

      <dl className="invitation__facts">
        <div>
          <dt>Para</dt>
          <dd>{invitation.email}</dd>
        </div>
        <div>
          <dt>Vigencia</dt>
          <dd>{expiryText(invitation.expiresAt)}</dd>
        </div>
      </dl>

      {problem && <Alert tone="danger">{problem}</Alert>}

      {!session ? (
        <div className="invitation__actions">
          <p className="auth__subtitle">Para entrar, crea tu cuenta o inicia sesión con {invitation.email}.</p>
          <LinkButton to={ACCOUNT_PATHS.signUp} state={{ from: here }} variant="primary">
            Crear mi cuenta
          </LinkButton>
          <LinkButton to={ACCOUNT_PATHS.signIn} state={{ from: here }}>
            Ya tengo cuenta
          </LinkButton>
        </div>
      ) : otherAccount ? (
        <div className="invitation__actions">
          <Alert tone="warning" title={`Entraste como ${signedAs}`}>
            <p>Esta invitación es para {invitation.email}. Cierra sesión y entra con esa cuenta para aceptarla.</p>
          </Alert>
          <Button variant="secondary" onClick={() => void signOut()}>
            Cerrar sesión
          </Button>
        </div>
      ) : (
        <div className="invitation__actions">
          <Button disabled={busy} onClick={() => void join()}>
            {busy ? "Entrando…" : `Aceptar y entrar a ${invitation.businessName}`}
          </Button>
        </div>
      )}
    </div>
  );
}
