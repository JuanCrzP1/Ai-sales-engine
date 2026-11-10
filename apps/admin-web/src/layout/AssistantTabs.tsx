import { NavLink } from "react-router-dom";
import { SectionStatusDot } from "../components/config/SectionStatusBadge";
import { Icon } from "../components/ui/Icon";
import { ASSISTANT_TABS } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import { useConfig } from "../state/useConfig";
import { NAV_ICONS } from "./navIcons";

/** Pestañas del Asistente IA: su resumen, su entrenamiento por partes, probarlo y publicarlo. Cada sección muestra su estado. */
export function AssistantTabs() {
  const pathTo = useWorkspacePath();
  const { progress } = useConfig();
  return (
    <div className="assistant-tabs">
      <p className="assistant-tabs__title">Asistente IA</p>
      <nav className="tabs" aria-label="Asistente IA">
        {ASSISTANT_TABS.map(({ item, label }) => {
          const section = progress.sections.find((entry) => entry.id === item.section);
          return (
            <NavLink key={item.key} to={pathTo(item.path)} className="tabs__link" end>
              <Icon name={NAV_ICONS[item.key]} size={16} />
              {label}
              {section && <SectionStatusDot progress={section} />}
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}
