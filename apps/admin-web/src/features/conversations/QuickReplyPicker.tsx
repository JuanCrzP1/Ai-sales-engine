import { Fragment, forwardRef, useEffect, useImperativeHandle, useRef, useState, type KeyboardEvent } from "react";
import { Link } from "react-router-dom";
import { groupByCategory, matchQuickReplies, replySummary, type QuickReply } from "../../domain/quickReplies/quickReplies";
import type { QuickRepliesState } from "../../state/useQuickReplies";

export interface QuickReplyPickerHandle {
  /** Las teclas desde el cuadro de texto («/prec» + ↑ ↓ Enter Escape). Dice si las usó. */
  handleKey(event: KeyboardEvent): boolean;
}

interface QuickReplyPickerProps {
  catalog: QuickRepliesState;
  /** Dónde se organizan (Configuración → Respuestas rápidas del negocio del chat). */
  managePath: string;
  /** Lo buscado. Con `searchable` se escribe aquí; sin él, llega de «/…» en el cuadro de texto. */
  query: string;
  searchable: boolean;
  onQuery: (query: string) => void;
  onPick: (reply: QuickReply) => void;
  onClose: () => void;
}

/**
 * Respuestas rápidas sobre el cuadro de texto del chat: solo buscar y usar. Agrupadas por categoría; se eligen con el mouse o con
 * ↑ ↓ y Enter. Se crean y editan en Configuración.
 */
export const QuickReplyPicker = forwardRef<QuickReplyPickerHandle, QuickReplyPickerProps>(function QuickReplyPicker(
  { catalog, managePath, query, searchable, onQuery, onPick, onClose },
  ref,
) {
  const [active, setActive] = useState(0);
  const box = useRef<HTMLDivElement>(null);
  const groups = groupByCategory(matchQuickReplies(catalog.replies, query));
  const visible = groups.flatMap((group) => group.replies);
  const grouped = groups.length > 1;

  useEffect(() => setActive(0), [query]);
  useEffect(() => {
    box.current?.querySelector<HTMLElement>(`[data-index="${active}"]`)?.scrollIntoView?.({ block: "nearest" });
  }, [active]);
  useEffect(() => {
    const onPointer = (event: PointerEvent) => {
      const target = event.target as HTMLElement;
      if (!box.current?.contains(target) && !target.closest("[data-quick-toggle], .composer__input")) onClose();
    };
    document.addEventListener("pointerdown", onPointer);
    return () => document.removeEventListener("pointerdown", onPointer);
  }, [onClose]);

  const handleKey = (event: KeyboardEvent): boolean => {
    if (event.key === "Escape") return (onClose(), true);
    if (visible.length === 0) return false;
    if (event.key === "ArrowDown") return (setActive((index) => (index + 1) % visible.length), true);
    if (event.key === "ArrowUp") return (setActive((index) => (index - 1 + visible.length) % visible.length), true);
    if ((event.key === "Enter" && !event.shiftKey) || event.key === "Tab") return (onPick(visible[Math.min(active, visible.length - 1)]!), true);
    return false;
  };
  useImperativeHandle(ref, () => ({ handleKey }));

  let index = -1;
  return (
    <div className="quick-picker" ref={box} role="dialog" aria-label="Respuestas rápidas">
      <header className="quick-picker__head">
        <h3 className="quick-picker__title">Respuestas rápidas</h3>
        {catalog.canManage && (
          <Link className="quick-picker__manage" to={managePath}>
            Administrar →
          </Link>
        )}
      </header>
      {searchable && (
        <input
          className="quick-picker__search"
          type="search"
          value={query}
          autoFocus
          placeholder="Buscar por atajo, categoría o texto…"
          aria-label="Buscar respuesta rápida"
          onChange={(event) => onQuery(event.target.value)}
          onKeyDown={(event) => {
            if (handleKey(event)) event.preventDefault();
          }}
        />
      )}
      <ul className="quick-picker__list" role="listbox" aria-label="Respuestas">
        {catalog.status === "loading" && <li className="quick-picker__hint">Cargando…</li>}
        {catalog.status === "error" && (
          <li className="quick-picker__hint">
            No se pudieron cargar.{" "}
            <button type="button" className="link-button" onClick={catalog.reload}>
              Reintentar
            </button>
          </li>
        )}
        {catalog.status === "ready" && catalog.replies.length === 0 && (
          <li className="quick-picker__hint">
            {catalog.canManage ? (
              <>
                Aún no hay respuestas rápidas. <Link to={managePath}>Crea la primera en Configuración</Link>.
              </>
            ) : (
              "Aún no hay respuestas rápidas. Las crea quien administra el negocio."
            )}
          </li>
        )}
        {catalog.status === "ready" && catalog.replies.length > 0 && visible.length === 0 && <li className="quick-picker__hint">Ninguna coincide con «{query}».</li>}
        {groups.map((group) => (
          <Fragment key={group.category}>
            {grouped && (
              <li className="quick-picker__group" role="presentation">
                {group.category}
              </li>
            )}
            {group.replies.map((reply) => {
              index += 1;
              const at = index;
              return (
                <li
                  key={reply.id}
                  data-index={at}
                  role="option"
                  aria-selected={at === active}
                  className={`quick-picker__item${at === active ? " quick-picker__item--active" : ""}`}
                  onMouseEnter={() => setActive(at)}
                >
                  <button type="button" className="quick-picker__pick" onClick={() => onPick(reply)}>
                    <strong>/{reply.shortcut}</strong>
                    <span>{replySummary(reply)}</span>
                    {reply.pieces.length > 1 && <em>{reply.pieces.length} mensajes</em>}
                  </button>
                </li>
              );
            })}
          </Fragment>
        ))}
      </ul>
      <p className="quick-picker__foot">
        Escribe <kbd>/</kbd> en el chat para buscarlas · <kbd>↑</kbd> <kbd>↓</kbd> y <kbd>Enter</kbd> para elegir
      </p>
    </div>
  );
});
