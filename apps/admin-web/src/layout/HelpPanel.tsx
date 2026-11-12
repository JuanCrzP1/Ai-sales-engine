import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Icon } from "../components/ui/Icon";
import { articlesForScreen, helpForPath } from "../domain/help/help";
import { HELP_ITEM, helpArticlePath, helpModulePath } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import { useHelpIndex, useHelpSearch } from "../state/useHelp";

/** Cuántos artículos de la pantalla se muestran antes de «Toda la ayuda de…». */
const SHOWN = 6;

/**
 * La ayuda de la pantalla abierta, al lado, sin salir de donde estás: el buscador y, sin búsqueda, los artículos de ESTA pantalla
 * (el que la explica, primero). Se abre con el botón de ayuda junto a los avisos; no hay botón flotante que tape el chat. Se cierra
 * con la X, con Escape, tocando fuera o al abrir un artículo. La ayuda se pide al abrirlo.
 */
export function HelpPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { pathname } = useLocation();
  const pathTo = useWorkspacePath();
  const [query, setQuery] = useState("");
  const index = useHelpIndex({ enabled: open });
  const results = useHelpSearch(open ? query : "");
  const search = useRef<HTMLInputElement>(null);
  const screen = helpForPath(pathname);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    search.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  const module = index.status === "ready" ? index.value.find((item) => item.id === screen.module) : undefined;
  const list = results?.status === "ready" ? results.value : articlesForScreen(module, screen).slice(0, SHOWN);

  return (
    <div className="help-panel__backdrop" role="presentation" onClick={onClose}>
      <aside className="help-panel" role="dialog" aria-modal="true" aria-label="Ayuda de esta pantalla" onClick={(event) => event.stopPropagation()}>
        <header className="help-panel__head">
          <div className="help-panel__title">
            <span>
              <strong>Ayuda</strong>
              {module && <small>Estás en {module.name}</small>}
            </span>
            <button type="button" className="help-panel__close" aria-label="Cerrar la ayuda" onClick={onClose}>
              <Icon name="close" size={18} />
            </button>
          </div>
          <label className="help-search help-search--compact">
            <Icon name="search" size={16} />
            <input
              ref={search}
              type="search"
              className="help-search__input"
              value={query}
              placeholder="Busca en la ayuda"
              aria-label="Buscar en la ayuda"
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
        </header>

        <div className="help-panel__body">
          <p className="help-panel__label" role="status">
            {results
              ? results.status === "ready"
                ? results.value.length === 0
                  ? `No encontramos nada con «${query.trim()}». Prueba con otras palabras.`
                  : `${results.value.length} ${results.value.length === 1 ? "resultado" : "resultados"}`
                : results.status === "error"
                  ? results.message
                  : "Buscando…"
              : index.status === "error"
                ? index.message
                : index.status === "loading"
                  ? "Cargando la ayuda…"
                  : `Para esta pantalla${module ? ` · ${module.name}` : ""}`}
          </p>
          <ul className="help-panel__list">
            {list.map((article) => (
              <li key={article.slug}>
                <Link className="help-panel__article" to={pathTo(helpArticlePath(article.slug))} onClick={onClose}>
                  <span className="help-panel__doc" aria-hidden="true">
                    <Icon name="file" size={16} />
                  </span>
                  <span className="help-panel__text">
                    <strong>{article.title}</strong>
                    <small>{article.summary}</small>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <nav className="help-panel__links" aria-label="Más ayuda">
            {module && (
              <Link to={pathTo(helpModulePath(module.id))} onClick={onClose}>
                Toda la ayuda de {module.name}
              </Link>
            )}
            <Link to={pathTo(HELP_ITEM.path)} onClick={onClose}>
              Abrir el Centro de ayuda
            </Link>
          </nav>
        </div>
      </aside>
    </div>
  );
}

/** El botón que abre la ayuda de la pantalla, junto a los avisos. */
export function HelpButton({ onOpen }: { onOpen: () => void }) {
  return (
    <button type="button" className="help-button" aria-label="Ayuda de esta pantalla" title="Ayuda de esta pantalla" onClick={onOpen}>
      <Icon name="question" size={18} />
    </button>
  );
}
