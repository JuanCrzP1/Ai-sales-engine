import { NavLink } from "react-router-dom";
import { Icon } from "../components/ui/Icon";
import { SETTINGS_TABS } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import { NAV_ICONS } from "./navIcons";

/** Pestañas de Ajustes: la inteligencia artificial y la atención humana del negocio. */
export function SettingsTabs() {
  const pathTo = useWorkspacePath();
  return (
    <div className="assistant-tabs">
      <p className="assistant-tabs__title">Ajustes</p>
      <nav className="tabs" aria-label="Ajustes">
        {SETTINGS_TABS.map((item) => (
          <NavLink key={item.key} to={pathTo(item.path)} className="tabs__link" end>
            <Icon name={NAV_ICONS[item.key]} size={16} />
            {item.title}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
