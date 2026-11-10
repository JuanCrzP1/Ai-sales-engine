import { NavLink } from "react-router-dom";
import { ASSISTANT_TABS } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";

/** Pestañas del Asistente IA: su entrenamiento por partes, probarlo y publicarlo. */
export function AssistantTabs() {
  const pathTo = useWorkspacePath();
  return (
    <div className="assistant-tabs">
      <p className="assistant-tabs__title">Asistente IA</p>
      <nav className="tabs" aria-label="Asistente IA">
        {ASSISTANT_TABS.map(({ item, label }) => (
          <NavLink key={item.key} to={pathTo(item.path)} className="tabs__link">
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
