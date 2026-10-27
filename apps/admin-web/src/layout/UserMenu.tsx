import { useEffect, useId, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Avatar } from "../components/ui/Avatar";
import { Icon } from "../components/ui/Icon";
import { ACCOUNT_PATHS } from "../navigation/accountPaths";
import { useAuth, useCurrentUser } from "../state/auth/useAuth";

/** Botón de cuenta con foto y nombre; despliega accesos a perfil y cierre de sesión. */
export function UserMenu() {
  const user = useCurrentUser();
  const { signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const location = useLocation();

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
        <span className="user-menu__name">{user.name}</span>
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
          <Link className="user-menu__item" to={ACCOUNT_PATHS.profile}>
            <Icon name="user" size={16} />
            Mi perfil
          </Link>
          <button type="button" className="user-menu__item user-menu__item--danger" onClick={() => void signOut()}>
            <Icon name="logout" size={16} />
            Cerrar sesión
          </button>
        </div>
      )}
    </div>
  );
}
