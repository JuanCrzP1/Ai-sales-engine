import type { ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { SectionStatusDot } from "../components/config/SectionStatusBadge";
import { BrandMark } from "../components/brand/BrandMark";
import { ProgressBar } from "../components/ui/Feedback";
import { Icon } from "../components/ui/Icon";
import { AI_ITEM, BUSINESSES_PATH, HOME_ITEM, PLAYGROUND_ITEM, REVIEW_ITEM, SECTION_ITEMS, type NavItem } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import { useConfig } from "../state/useConfig";
import { NAV_ICONS } from "./navIcons";

interface SidebarProps {
  id: string;
  open: boolean;
}

export function Sidebar({ id, open }: SidebarProps) {
  const { progress, document } = useConfig();

  return (
    <aside id={id} className={`sidebar${open ? " sidebar--open" : ""}`} aria-label="Menú principal">
      <div className="sidebar__brand">
        <BrandMark />
        <div className="sidebar__brand-text">
          <span className="sidebar__brand-name">AI Sales Engine</span>
          <span className="sidebar__brand-sub">{document.identity.name.trim() || "Tu asistente de ventas"}</span>
        </div>
      </div>

      <Link to={BUSINESSES_PATH} className="sidebar__back">
        ← Todos los negocios
      </Link>

      <div className="sidebar__progress">
        <ProgressBar value={progress.completed} total={progress.total} label="Secciones listas" />
      </div>

      <nav className="nav" aria-label="Secciones de configuración">
        <NavEntry item={HOME_ITEM} end />
        <p className="nav__heading" aria-hidden="true">
          Configuración
        </p>
        {SECTION_ITEMS.map((item) => {
          const sectionProgress = progress.sections.find((section) => section.id === item.section);
          return (
            <NavEntry key={item.key} item={item}>
              {sectionProgress && <SectionStatusDot progress={sectionProgress} />}
            </NavEntry>
          );
        })}
        <div className="nav__divider" role="presentation" />
        <NavEntry item={REVIEW_ITEM} />
        <p className="nav__heading" aria-hidden="true">
          Asistente
        </p>
        <NavEntry item={AI_ITEM} />
        <NavEntry item={PLAYGROUND_ITEM} />
      </nav>
    </aside>
  );
}

function NavEntry({ item, end, children }: { item: NavItem; end?: boolean; children?: ReactNode }) {
  const pathTo = useWorkspacePath();
  return (
    <NavLink to={pathTo(item.path)} end={end} className="nav__link">
      <span className="nav__icon">
        <Icon name={NAV_ICONS[item.key]} />
      </span>
      <span className="nav__label">{item.title}</span>
      {children}
    </NavLink>
  );
}
