import { useEffect, useRef } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Icon } from "../components/ui/Icon";
import { ACCOUNT_GROUPS, SETTINGS_GROUPS, allowed, type SettingsGroup } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import { useAuth } from "../state/auth/useAuth";
import { useBusinessRole } from "../state/roleContext";
import { NAV_ICONS } from "./navIcons";

/**
 * Una sección con su propio menú a la izquierda y la página abierta a la derecha (en el celular, una fila de pestañas que se
 * desliza de lado). La usan Configuración (lo del negocio) y Mi cuenta (lo de la persona). Lo que aún no existe se ve con «Pronto».
 */
function SectionMenuLayout({ label, title, subtitle, groups }: { label: string; title: string; subtitle: string; groups: SettingsGroup[] }) {
  const pathTo = useWorkspacePath();
  const { verifiesCredentials } = useAuth();
  const role = useBusinessRole();
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
      <nav ref={nav} className="settings-nav" aria-label={label}>
        <p className="settings-nav__title">{title}</p>
        <p className="settings-nav__subtitle">{subtitle}</p>
        {groups.map((group) => {
          const entries = group.entries.filter((entry) => (!entry.account || verifiesCredentials) && allowed(entry.item, role));
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

/** Configuración: solo lo del negocio abierto (su asistente y su facturación). */
export function SettingsLayout() {
  return <SectionMenuLayout label="Configuración" title="Configuración" subtitle="De este negocio" groups={SETTINGS_GROUPS} />;
}

/** Mi cuenta: lo de la persona, igual en todos sus negocios. */
export function AccountLayout() {
  return <SectionMenuLayout label="Mi cuenta" title="Mi cuenta" subtitle="Igual en todos tus negocios" groups={ACCOUNT_GROUPS} />;
}
