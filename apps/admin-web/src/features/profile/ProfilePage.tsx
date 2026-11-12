import { Navigate } from "react-router-dom";
import { LinkButton } from "../../components/ui/Button";
import { Card, PageHeader } from "../../components/ui/Layout";
import { StandalonePage } from "../../layout/StandalonePage";
import { ATTENTION_ITEM, ENTRY_PATH, NOTIFICATIONS_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useAuth } from "../../state/auth/useAuth";
import { AvatarEditor } from "./AvatarEditor";
import { DevicePushPanel } from "./DevicePushPanel";
import { PasswordCard } from "./PasswordCard";
import { ProfileDetailsForm } from "./ProfileDetailsForm";
import { SessionCard } from "./SessionCard";

/**
 * Mi cuenta: lo de la persona, igual en todos sus negocios. Dentro de un negocio son tres páginas con su menú (Mi perfil,
 * Seguridad, Notificaciones); fuera de un negocio (antes de crear el primero), una sola página con todo. Perfil y seguridad solo
 * existen con cuentas reales: el acceso local no tiene cuenta que editar.
 */
export function ProfilePage() {
  const { verifiesCredentials } = useAuth();
  if (!verifiesCredentials) return <Navigate to={ENTRY_PATH} replace />;

  return (
    <StandalonePage>
      <PageHeader eyebrow="Mi cuenta" title="Mi cuenta" description="Tu perfil, tu contraseña y tus avisos. Son tuyos: los mismos en todos tus negocios." actions={<LinkButton to={ENTRY_PATH}>Volver al panel</LinkButton>} />
      <div className="settings-stack">
        <AvatarEditor />
        <ProfileDetailsForm />
        <PasswordCard />
        <SessionCard />
        <Card icon="bell" tone="amber" title="Notificaciones">
          <DevicePushPanel />
        </Card>
      </div>
    </StandalonePage>
  );
}

/** Mi cuenta → Mi perfil. */
export function AccountProfilePage() {
  const { verifiesCredentials } = useAuth();
  const pathTo = useWorkspacePath();
  if (!verifiesCredentials) return <Navigate to={pathTo(NOTIFICATIONS_ITEM.path)} replace />;

  return (
    <>
      <PageHeader title="Mi perfil" description="Tu foto y tus datos. Son de tu cuenta: los mismos en todos tus negocios." />
      <div className="settings-stack">
        <AvatarEditor />
        <ProfileDetailsForm />
      </div>
    </>
  );
}

/** Mi cuenta → Seguridad: la contraseña y las sesiones abiertas. */
export function SecurityPage() {
  const { verifiesCredentials } = useAuth();
  const pathTo = useWorkspacePath();
  if (!verifiesCredentials) return <Navigate to={pathTo(NOTIFICATIONS_ITEM.path)} replace />;

  return (
    <>
      <PageHeader title="Seguridad" description="Tu contraseña y dónde tienes la sesión abierta." />
      <div className="settings-stack">
        <PasswordCard />
        <SessionCard />
      </div>
    </>
  );
}

/**
 * Mi cuenta → Notificaciones: los avisos en los dispositivos de la persona. Los correos de avisos son de cada negocio: se configuran
 * en su Atención humana.
 */
export function NotificationsPage() {
  const pathTo = useWorkspacePath();
  return (
    <>
      <PageHeader title="Notificaciones" description="Para enterarte al instante cuando un cliente necesita a una persona, aunque no tengas el panel abierto." />
      <div className="settings-stack">
        <Card
          icon="bell"
          tone="amber"
          title="En este dispositivo"
          description="Suenan como un mensaje de WhatsApp aunque el panel esté cerrado. Actívalas en cada celular o computador donde atiendes."
        >
          <DevicePushPanel header={false} />
        </Card>
        <Card icon="mail" tone="sky" title="Por correo" description="Los avisos por correo son de cada negocio: a qué correo llegan y si se envían.">
          <div>
            <LinkButton variant="secondary" to={pathTo(ATTENTION_ITEM.path)}>
              Configurar en Atención humana
            </LinkButton>
          </div>
        </Card>
      </div>
    </>
  );
}
