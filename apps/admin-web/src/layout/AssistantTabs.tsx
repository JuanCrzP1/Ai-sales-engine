import { Fragment } from "react";
import { NavLink } from "react-router-dom";
import { SectionStatusDot } from "../components/config/SectionStatusBadge";
import { Icon } from "../components/ui/Icon";
import { ASSISTANT_TABS, PLAYGROUND_ITEM } from "../navigation/navItems";
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
        {ASSISTANT_TABS.map(({ item, label, short }) => {
          const section = progress.sections.find((entry) => entry.id === item.section);
          // Con nombre corto («Productos»), el resto del nombre («y servicios») queda para los lectores de pantalla.
          const visible = short && label.startsWith(short) ? short : label;
          return (
            <Fragment key={item.key}>
              {item.key === PLAYGROUND_ITEM.key && <span className="tabs__spacer" aria-hidden="true" />}
              <NavLink to={pathTo(item.path)} className={`tabs__link${section ? "" : " tabs__link--tool"}`} title={visible !== label ? label : undefined} end>
                <Icon name={NAV_ICONS[item.key]} size={16} />
                {visible}
                {visible !== label && (
                  <>
                    {" "}
                    <span className="visually-hidden">{label.slice(visible.length).trim()}</span>
                  </>
                )}
                {section && <SectionStatusDot progress={section} />}
              </NavLink>
            </Fragment>
          );
        })}
      </nav>
    </div>
  );
}
