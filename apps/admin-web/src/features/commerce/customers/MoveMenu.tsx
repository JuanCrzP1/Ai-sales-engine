import { useEffect, useRef, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import { Icon } from "../../../components/ui/Icon";
import { BOARD_STAGES, STAGE_LABELS, type BoardStage } from "../../../domain/commerce/types";

/**
 * «Mover a…»: la otra forma de cambiar de etapa, además de arrastrar (con teclado, con lector de pantalla y en el celular). La lista
 * se dibuja al final de la página (un portal), como los diálogos: el tablero recorta lo que se sale de él. Escape, tocar fuera o
 * desplazarse la cierra.
 */
export function MoveMenu({ current, label, disabled = false, onMove }: { current: BoardStage; label: string; disabled?: boolean; onMove: (stage: BoardStage) => void }) {
  const [open, setOpen] = useState(false);
  const [place, setPlace] = useState<CSSProperties>({});
  const root = useRef<HTMLSpanElement>(null);
  const list = useRef<HTMLSpanElement>(null);

  const toggle = () => {
    const rect = root.current?.getBoundingClientRect();
    if (rect) {
      // Debajo del botón si cabe; si no, encima.
      const height = 44 + BOARD_STAGES.length * 38;
      const below = rect.bottom + 6 + height <= window.innerHeight;
      setPlace({ right: Math.max(8, window.innerWidth - rect.right), ...(below ? { top: rect.bottom + 6 } : { bottom: window.innerHeight - rect.top + 6 }) });
    }
    setOpen((value) => !value);
  };

  useEffect(() => {
    if (!open) return;
    const outside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (!root.current?.contains(target) && !list.current?.contains(target)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    const dismiss = () => setOpen(false);
    document.addEventListener("mousedown", outside);
    document.addEventListener("keydown", escape);
    window.addEventListener("scroll", dismiss, true);
    return () => {
      document.removeEventListener("mousedown", outside);
      document.removeEventListener("keydown", escape);
      window.removeEventListener("scroll", dismiss, true);
    };
  }, [open]);

  return (
    <span className="move-menu" ref={root}>
      <button type="button" className="move-menu__trigger" aria-haspopup="menu" aria-expanded={open} aria-label={label} title="Mover a…" disabled={disabled} onClick={toggle}>
        <Icon name="arrowRight" size={15} />
      </button>
      {open &&
        createPortal(
          <span className="move-menu__list" role="menu" ref={list} style={place}>
            <span className="move-menu__title">Mover a</span>
            {BOARD_STAGES.map((stage) => (
              <button
                key={stage}
                type="button"
                role="menuitem"
                className={`move-menu__item stage-tone--${stage}`}
                disabled={stage === current}
                onClick={() => {
                  setOpen(false);
                  onMove(stage);
                }}
              >
                <span className="move-menu__dot" aria-hidden="true" />
                {STAGE_LABELS[stage]}
                {stage === current && <span className="move-menu__here">aquí</span>}
                {stage === "customer" && stage !== current && <span className="move-menu__here">con su venta</span>}
              </button>
            ))}
          </span>,
          document.body,
        )}
    </span>
  );
}
