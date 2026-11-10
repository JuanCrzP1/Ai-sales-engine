import type { ReactNode } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { BrandMark } from "../components/brand/BrandMark";
import { Icon } from "../components/ui/Icon";
import { ASSISTANT_HUB_ITEM, CHANNELS_ITEM, isAssistantPath, MAIN_ITEMS, SETTINGS_ITEM, type NavItem } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import { useConfig } from "../state/useConfig";
import { BusinessSwitcher } from "./BusinessSwitcher";
import { NAV_ICONS } from "./navIcons";

interface SidebarProps {
  id: string;
  open: boolean;
}

/** Menú del negocio: primero atender y vender; después, su configuración. */
export function Sidebar({ id, open }: SidebarProps) {
  const { progress } = useConfig();
  const { pathname } = useLocation();
  const pending = progress.total - progress.completed;

  return (
    <aside id={id} className={`sidebar${open ? " sidebar--open" : ""}`} aria-label="Menú principal">
      <div className="sidebar__brand">
        <BrandMark />
        <div className="sidebar__brand-text">
          <span className="sidebar__brand-name">AI Sales Engine</span>
          <span className="sidebar__brand-sub">Tu asistente de ventas</span>
        </div>
      </div>

      <BusinessSwitcher />

      <nav className="nav" aria-label="Menú del negocio">
        {MAIN_ITEMS.map((item) => (
          <NavEntry key={item.key} item={item} end={item.key === "home"} />
        ))}
        <p className="nav__heading" aria-hidden="true">
          Configuración
        </p>
        <NavEntry item={ASSISTANT_HUB_ITEM} active={isAssistantPath(pathname)}>
          {pending > 0 && (
            <span className="nav__count" title={`${pending} ${pending === 1 ? "sección pendiente" : "secciones pendientes"}`}>
              {pending}
            </span>
          )}
        </NavEntry>
        <NavEntry item={CHANNELS_ITEM} />
        <NavEntry item={SETTINGS_ITEM} />
      </nav>
    </aside>
  );
}

function NavEntry({ item, end, active, children }: { item: NavItem; end?: boolean; active?: boolean; children?: ReactNode }) {
  const pathTo = useWorkspacePath();
  const content = (
    <>
      <span className="nav__icon">
        <Icon name={NAV_ICONS[item.key]} />
      </span>
      <span className="nav__label">{item.title}</span>
      {children}
    </>
  );
  // El Asistente IA tiene varias pestañas: su entrada queda marcada en todas, no solo en la primera.
  if (active !== undefined) {
    return (
      <Link to={pathTo(item.path)} className="nav__link" aria-current={active ? "page" : undefined}>
        {content}
      </Link>
    );
  }
  return (
    <NavLink to={pathTo(item.path)} end={end} className="nav__link">
      {content}
    </NavLink>
  );
}
