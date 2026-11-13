import { useRef, type ReactNode, type TouchEvent } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { BrandMark } from "../components/brand/BrandMark";
import { Icon } from "../components/ui/Icon";
import {
  ASSISTANT_HUB_ITEM,
  CHANNELS_ITEM,
  HELP_ITEM,
  INTEGRATIONS_ITEM,
  isAssistantPath,
  isHelpCenterPath,
  isIntegrationsPath,
  isSettingsPath,
  MAIN_ITEMS,
  SETTINGS_ITEM,
  allowed,
  type NavItem,
} from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import { useAuth } from "../state/auth/useAuth";
import { useConfig } from "../state/useConfig";
import { useBusinessRole } from "../state/roleContext";
import { BusinessSwitcher } from "./BusinessSwitcher";
import { HelpButton } from "./HelpPanel";
import { NAV_ICONS } from "./navIcons";
import { NotificationBell } from "./NotificationBell";
import { UserMenu } from "./UserMenu";

interface SidebarProps {
  id: string;
  open: boolean;
  /** Celular: el menú es un panel que se desliza, con su botón de cerrar; los avisos están en la barra superior. */
  compact?: boolean;
  onClose?: () => void;
  /** Abre la ayuda de la pantalla (junto a los avisos). */
  onOpenHelp?: () => void;
}

/** Cuánto hay que deslizar el panel hacia la izquierda para cerrarlo. */
const SWIPE_TO_CLOSE = 60;

/**
 * Menú del negocio: primero atender y vender; después, su configuración. Como en Slack o Linear, los avisos van junto a la marca y
 * la cuenta abajo: el contenido no pierde alto con una barra superior.
 */
export function Sidebar({ id, open, compact = false, onClose, onOpenHelp }: SidebarProps) {
  const { progress, publication } = useConfig();
  const { verifiesCredentials } = useAuth();
  const { pathname } = useLocation();
  const role = useBusinessRole();
  const pending = progress.total - progress.completed;
  const unpublished = publication === "pending";
  const touchStart = useRef<number | null>(null);

  const onTouchStart = (event: TouchEvent) => {
    touchStart.current = event.touches[0]?.clientX ?? null;
  };
  const onTouchEnd = (event: TouchEvent) => {
    const start = touchStart.current;
    touchStart.current = null;
    const end = event.changedTouches[0]?.clientX;
    if (compact && start !== null && end !== undefined && start - end > SWIPE_TO_CLOSE) onClose?.();
  };

  return (
    <aside
      id={id}
      className={`sidebar${open ? " sidebar--open" : ""}`}
      aria-label="Menú principal"
      role={compact ? "dialog" : undefined}
      aria-modal={compact && open ? true : undefined}
      onTouchStart={compact ? onTouchStart : undefined}
      onTouchEnd={compact ? onTouchEnd : undefined}
    >
      <div className="sidebar__brand">
        <BrandMark />
        <div className="sidebar__brand-text">
          <span className="sidebar__brand-name">AI Sales Engine</span>
          <span className="sidebar__brand-sub">Tu asistente de ventas</span>
        </div>
        {compact ? (
          <button type="button" className="sidebar__close" aria-label="Cerrar menú" onClick={onClose}>
            <Icon name="close" size={18} />
          </button>
        ) : (
          <span className="sidebar__actions">
            {onOpenHelp && <HelpButton onOpen={onOpenHelp} />}
            <NotificationBell />
          </span>
        )}
      </div>

      <BusinessSwitcher />

      <nav className="nav" aria-label="Menú del negocio">
        {MAIN_ITEMS.filter((item) => allowed(item, role)).map((item) => (
          <NavEntry key={item.key} item={item} end={item.key === "home"} />
        ))}
        {/* Un asesor solo atiende: «Tu negocio» (asistente, canales e integraciones) es de quien lo configura. */}
        {allowed(ASSISTANT_HUB_ITEM, role) && (
          <>
            <p className="nav__heading" aria-hidden="true">
              Tu negocio
            </p>
            <NavEntry item={ASSISTANT_HUB_ITEM} active={isAssistantPath(pathname)}>
              {unpublished && <span className="nav__dot" role="img" aria-label="Cambios sin publicar" title="Tienes cambios guardados que tus clientes todavía no ven" />}
              {pending > 0 && (
                <span className="nav__count" title={`${pending} ${pending === 1 ? "sección pendiente" : "secciones pendientes"}`}>
                  {pending}
                </span>
              )}
            </NavEntry>
            <NavEntry item={CHANNELS_ITEM} />
            <NavEntry item={INTEGRATIONS_ITEM} active={isIntegrationsPath(pathname)} />
          </>
        )}
        {/* Como en las plataformas serias: la configuración del negocio va sola, fija abajo. Lo personal está en el menú de la foto. */}
        <div className="nav__bottom">
          <NavEntry item={HELP_ITEM} active={isHelpCenterPath(pathname)} />
          <NavEntry item={SETTINGS_ITEM} active={isSettingsPath(pathname)} />
        </div>
      </nav>

      {verifiesCredentials && (
        <div className="sidebar__footer">
          <UserMenu />
        </div>
      )}
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
