import { useEffect, useRef } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Icon } from "../components/ui/Icon";
import { SETTINGS_GROUPS } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import { useAuth } from "../state/auth/useAuth";
import { NAV_ICONS } from "./navIcons";

/**
 * Configuración: su propio menú por grupos (Cuenta, Asistente, Facturación) a la izquierda y la sección abierta a la derecha. En el
 * celular, el menú es una fila de pestañas que se desliza de lado. Lo que aún no existe se ve con «Pronto».
 */
export function SettingsLayout() {
  const pathTo = useWorkspacePath();
  const { verifiesCredentials } = useAuth();
  const { pathname } = useLocation();
  const nav = useRef<HTMLElement>(null);

  // En el celular, la sección abierta queda a la vista dentro de la fila de pestañas.
  useEffect(() => {
    const strip = nav.current;
    const active = strip?.querySelector<HTMLElement>('[aria-current="page"]');
    if (!strip || !active || strip.scrollWidth <= strip.clientWidth) return;
    strip.scrollLeft = active.offsetLeft - (strip.clientWidth - active.offsetWidth) / 2;
  }, [pathname]);

  return (
    <div className="settings-layout">
      <nav ref={nav} className="settings-nav" aria-label="Configuración">
        <p className="settings-nav__title">Configuración</p>
        {SETTINGS_GROUPS.map((group) => {
          const entries = group.entries.filter((entry) => !entry.account || verifiesCredentials);
          if (entries.length === 0) return null;
          return (
            <div className="settings-nav__group" key={group.title}>
              <p className="settings-nav__heading">{group.title}</p>
              {entries.map(({ item, description, soon }) => (
                <NavLink key={item.key} to={pathTo(item.path)} className="settings-nav__link" end>
                  <span className="settings-nav__icon" aria-hidden="true">
                    <Icon name={NAV_ICONS[item.key]} size={18} />
                  </span>
                  <span className="settings-nav__text">
                    <span className="settings-nav__label">
                      {item.title}
                      {soon && <span className="soon-badge">Pronto</span>}
                    </span>
                    <span className="settings-nav__description">{description}</span>
                  </span>
                </NavLink>
              ))}
            </div>
          );
        })}
      </nav>
      <div className="settings-layout__content">
        <Outlet />
      </div>
    </div>
  );
}
