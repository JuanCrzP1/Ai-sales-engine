import { Navigate } from "react-router-dom";
import { LinkButton } from "../../components/ui/Button";
import { PageHeader } from "../../components/ui/Layout";
import { StandalonePage } from "../../layout/StandalonePage";
import { ENTRY_PATH } from "../../navigation/navItems";
import { useAuth } from "../../state/auth/useAuth";
import { AvatarEditor } from "./AvatarEditor";
import { ProfileDetailsForm } from "./ProfileDetailsForm";
import { SessionCard } from "./SessionCard";

/** Perfil de la cuenta. Solo tiene sentido con autenticación real; el acceso local no tiene cuenta que editar. */
export function ProfilePage() {
  const { verifiesCredentials } = useAuth();
  if (!verifiesCredentials) return <Navigate to={ENTRY_PATH} replace />;

  return (
    <StandalonePage>
      <PageHeader eyebrow="Cuenta" title="Mi perfil" description="Tu foto, tus datos y tu sesión." actions={<LinkButton to={ENTRY_PATH}>Volver al panel</LinkButton>} />
      <AvatarEditor />
      <ProfileDetailsForm />
      <SessionCard />
    </StandalonePage>
  );
}
