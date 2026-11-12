import { useId, useRef, type KeyboardEvent, type ReactNode } from "react";

export interface TabItem {
  value: string;
  label: ReactNode;
}

interface TabsProps {
  label: string;
  tabs: TabItem[];
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
}

/**
 * Pestañas accesibles (patrón WAI-ARIA): la lista con su nombre, cada pestaña ligada a su panel y las flechas, Inicio y Fin para
 * moverse con el teclado. Solo se muestra el panel de la pestaña elegida (`children`).
 */
export function Tabs({ label, tabs, value, onChange, children }: TabsProps) {
  const base = useId();
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  const current = Math.max(0, tabs.findIndex((tab) => tab.value === value));

  const move = (event: KeyboardEvent) => {
    const last = tabs.length - 1;
    const next =
      event.key === "ArrowRight" ? (current === last ? 0 : current + 1)
      : event.key === "ArrowLeft" ? (current === 0 ? last : current - 1)
      : event.key === "Home" ? 0
      : event.key === "End" ? last
      : null;
    if (next === null) return;
    event.preventDefault();
    onChange(tabs[next]!.value);
    buttons.current[next]?.focus();
  };

  return (
    <div className="pane-tabs">
      <div className="pane-tabs__list" role="tablist" aria-label={label} onKeyDown={move}>
        {tabs.map((tab, index) => {
          const selected = index === current;
          return (
            <button
              key={tab.value}
              ref={(element) => {
                buttons.current[index] = element;
              }}
              type="button"
              role="tab"
              id={`${base}-tab-${tab.value}`}
              aria-selected={selected}
              aria-controls={`${base}-panel`}
              tabIndex={selected ? 0 : -1}
              className={`pane-tabs__tab${selected ? " pane-tabs__tab--active" : ""}`}
              onClick={() => onChange(tab.value)}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      <div className="pane-tabs__panel" role="tabpanel" id={`${base}-panel`} aria-labelledby={`${base}-tab-${tabs[current]?.value}`}>
        {children}
      </div>
    </div>
  );
}
