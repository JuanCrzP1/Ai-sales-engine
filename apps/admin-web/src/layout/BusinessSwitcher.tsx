import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Icon } from "../components/ui/Icon";
import type { BusinessSummary } from "../domain/config/types";
import { initials } from "../domain/inbox/format";
import { BUSINESSES_PATH, NEW_BUSINESS_PATH, workspacePath } from "../navigation/navItems";
import { useBusinessDirectory } from "../state/directoryContext";
import { useConfig } from "../state/useConfig";

/** El negocio en el que se trabaja, arriba del menú: abre la lista de los negocios del usuario para cambiar o crear otro. */
export function BusinessSwitcher() {
  const directory = useBusinessDirectory();
  const { slug = "" } = useParams();
  const { document } = useConfig();
  const [open, setOpen] = useState(false);
  const [businesses, setBusinesses] = useState<BusinessSummary[] | null>(null);
  const root = useRef<HTMLDivElement>(null);
  const name = document.identity.name.trim() || slug;

  useEffect(() => {
    if (!open) return;
    let active = true;
    directory.list().then(
      (loaded) => active && setBusinesses(loaded),
      () => active && setBusinesses([]),
    );
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === "Escape" : !root.current?.contains(event.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", close);
    window.addEventListener("keydown", close);
    return () => {
      active = false;
      window.removeEventListener("mousedown", close);
      window.removeEventListener("keydown", close);
    };
  }, [open, directory]);

  return (
    <div className="switcher" ref={root}>
      <button type="button" className="switcher__button" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        <span className="switcher__avatar" aria-hidden="true">
          {initials(name)}
        </span>
        <span className="switcher__text">
          <span className="switcher__label">Negocio</span>
          <span className="switcher__name">{name}</span>
        </span>
        <Icon name="chevronDown" size={16} />
      </button>
      {open && (
        <div className="switcher__menu" role="menu" aria-label="Tus negocios">
          {businesses === null && <p className="switcher__hint">Cargando negocios…</p>}
          {businesses?.map((business) => (
            <Link
              key={business.slug}
              role="menuitem"
              to={workspacePath(business.slug)}
              className={`switcher__item${business.slug === slug ? " switcher__item--current" : ""}`}
              aria-current={business.slug === slug ? "true" : undefined}
              onClick={() => setOpen(false)}
            >
              <span className="switcher__avatar switcher__avatar--small" aria-hidden="true">
                {initials(business.name)}
              </span>
              <span className="switcher__item-name">{business.name}</span>
              {business.slug === slug && <Icon name="check" size={16} />}
            </Link>
          ))}
          <div className="switcher__divider" role="separator" />
          <Link role="menuitem" to={NEW_BUSINESS_PATH} className="switcher__item" onClick={() => setOpen(false)}>
            <span className="switcher__avatar switcher__avatar--small switcher__avatar--add" aria-hidden="true">
              <Icon name="plus" size={14} />
            </span>
            <span className="switcher__item-name">Crear negocio</span>
          </Link>
          {directory.canImportExisting && (
            <Link role="menuitem" to={BUSINESSES_PATH} className="switcher__item" onClick={() => setOpen(false)}>
              <span className="switcher__avatar switcher__avatar--small switcher__avatar--add" aria-hidden="true">
                <Icon name="settings" size={14} />
              </span>
              <span className="switcher__item-name">Administrar negocios</span>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
