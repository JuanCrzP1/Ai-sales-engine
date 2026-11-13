import { Navigate, Outlet } from "react-router-dom";
import { LinkButton } from "../components/ui/Button";
import { Icon } from "../components/ui/Icon";
import { ROLE_LABELS, type Capability } from "../domain/team/team";
import { CONVERSATIONS_ITEM, SETTINGS_GROUPS, allowed } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import { useAuth } from "../state/auth/useAuth";
import { useBusinessRole } from "../state/roleContext";

const REASONS: Record<Capability, string> = {
  attend: "No tienes acceso a esta pantalla.",
  reports: "Los reportes son del dueño o de un administrador.",
  configure: "Configurar el negocio es del dueño o de un administrador. Si necesitas cambiar algo, pídeselo a uno de ellos.",
  team: "Administrar el equipo es del dueño o de un administrador.",
  deleteBusiness: "Solo el dueño del negocio puede hacer esto.",
};

/**
 * Las pantallas que el rol no permite: quien llega con un enlace guardado ve por qué no puede y a dónde ir, en vez de una pantalla
 * que falla. El menú ya no las muestra, y el servidor las rechaza de todos modos.
 */
export function RequireCapability({ need }: { need: Capability }) {
  const role = useBusinessRole();
  const pathTo = useWorkspacePath();
  if (allowed({ key: "home", path: "", title: "", need }, role)) return <Outlet />;
  return (
    <section className="role-wall" aria-labelledby="sin-permiso">
      <span className="role-wall__icon" aria-hidden="true">
        <Icon name="shield" size={22} />
      </span>
      <h1 id="sin-permiso" className="role-wall__title">
        Tu rol no permite ver esta pantalla
      </h1>
      <p className="role-wall__text">
        Eres {ROLE_LABELS[role]} en este negocio. {REASONS[need]}
      </p>
      <LinkButton to={pathTo(CONVERSATIONS_ITEM.path)}>Ir a Conversaciones</LinkButton>
    </section>
  );
}

/** «Configuración» abre la primera opción que el rol puede ver (para un asesor, sus respuestas rápidas). */
export function SettingsIndex() {
  const role = useBusinessRole();
  const { verifiesCredentials } = useAuth();
  const first = SETTINGS_GROUPS.flatMap((group) => group.entries).find((entry) => (!entry.account || verifiesCredentials) && !entry.soon && allowed(entry.item, role));
  return <Navigate to={first ? first.item.path.split("/").pop()! : `../${CONVERSATIONS_ITEM.path}`} replace />;
}
