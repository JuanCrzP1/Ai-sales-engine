import { useEffect, useId, useRef, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { Avatar } from "../components/ui/Avatar";
import { Icon, type IconName } from "../components/ui/Icon";
import { ACCOUNT_PATHS } from "../navigation/accountPaths";
import { ACCOUNT_PROFILE_ITEM, NOTIFICATIONS_ITEM, SECURITY_ITEM, type NavItem } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import { useAuth, useCurrentUser } from "../state/auth/useAuth";

const ACCOUNT_LINKS: { item: NavItem; icon: IconName; title?: string }[] = [
  { item: ACCOUNT_PROFILE_ITEM, icon: "user" },
  { item: SECURITY_ITEM, icon: "shield" },
  { item: NOTIFICATIONS_ITEM, icon: "bell" },
];

/** La cuenta, abajo en la barra lateral: foto, nombre y correo; despliega hacia arriba Mi cuenta (perfil, seguridad, notificaciones) y el cierre de sesión. */
export function UserMenu() {
  const user = useCurrentUser();
  const { signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const location = useLocation();
  const pathTo = useWorkspacePath();
  // Dentro de un negocio, el perfil vive en su Configuración; fuera (crear el primer negocio), en su propia página.
  const inBusiness = Boolean(useParams().slug);

  useEffect(() => setOpen(false), [location.pathname]);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: PointerEvent) => {
      if (event.target instanceof Node && !rootRef.current?.contains(event.target)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      triggerRef.current?.focus();
    };
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="user-menu" ref={rootRef}>
      <button
        ref={triggerRef}
        type="button"
        className="user-menu__trigger"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={`Cuenta de ${user.name}`}
        onClick={() => setOpen((current) => !current)}
      >
        <Avatar name={user.name} src={user.avatarUrl} size="sm" />
        <span className="user-menu__who">
          <span className="user-menu__name">{user.name}</span>
          <span className="user-menu__email">{user.email}</span>
        </span>
        <Icon name="chevronDown" size={16} />
      </button>

      {open && (
        <div className="user-menu__panel" id={panelId}>
          <div className="user-menu__header">
            <Avatar name={user.name} src={user.avatarUrl} size="md" />
            <div className="user-menu__identity">
              <strong>{user.name}</strong>
              <span>{user.email}</span>
            </div>
          </div>
          {/* Solo lo de la persona: lo del negocio está en Configuración, abajo en el menú de la izquierda. */}
          {(inBusiness ? ACCOUNT_LINKS : [{ item: ACCOUNT_PROFILE_ITEM, icon: "user" as const, title: "Mi cuenta" }]).map(({ item, icon, title }) => (
            <Link key={item.key} className="user-menu__item" to={inBusiness ? pathTo(item.path) : ACCOUNT_PATHS.profile}>
              <Icon name={icon} size={16} />
              {title ?? item.title}
            </Link>
          ))}
          <div className="user-menu__separator" role="separator" />
          <button type="button" className="user-menu__item user-menu__item--danger" onClick={() => void signOut()}>
            <Icon name="logout" size={16} />
            Cerrar sesión
          </button>
        </div>
      )}
    </div>
  );
}
