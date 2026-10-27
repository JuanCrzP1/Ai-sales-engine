import { useId, useRef, useState, type ReactNode } from "react";
import { Button } from "./Button";

interface ListEditorProps {
  label: string;
  hint?: ReactNode;
  items: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
  addLabel?: string;
  emptyText?: string;
}

/** Lista editable de textos cortos (agregar, editar en línea y quitar). */
export function ListEditor({ label, hint, items, onChange, placeholder, addLabel = "Agregar", emptyText }: ListEditorProps) {
  const [draft, setDraft] = useState("");
  const id = useId();
  const keys = useStableKeys(items.length);

  const add = () => {
    const value = draft.trim();
    if (!value) return;
    keys.append();
    onChange([...items, value]);
    setDraft("");
  };

  const remove = (index: number) => {
    keys.remove(index);
    onChange(items.filter((_, i) => i !== index));
  };

  return (
    <div className="field">
      <label className="field__label" htmlFor={`${id}-new`}>
        {label}
      </label>
      {hint && <p className="field__hint">{hint}</p>}
      <div className="list-editor">
        {items.length === 0 && emptyText && <p className="field__hint">{emptyText}</p>}
        {items.map((item, index) => (
          <div className="list-editor__row" key={keys.at(index)}>
            <input
              className="input"
              value={item}
              aria-label={`${label}: elemento ${index + 1}`}
              onChange={(event) => onChange(items.map((current, i) => (i === index ? event.target.value : current)))}
            />
            <Button variant="danger" size="small" onClick={() => remove(index)} aria-label={`Quitar de ${label}: elemento ${index + 1}`}>
              Quitar
            </Button>
          </div>
        ))}
        <div className="list-editor__add">
          <input
            id={`${id}-new`}
            className="input"
            value={draft}
            placeholder={placeholder}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                add();
              }
            }}
          />
          <Button variant="secondary" onClick={add} disabled={!draft.trim()}>
            {addLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}

/**
 * Claves estables para una lista de textos sin identificadores: se conservan al editar
 * y se reasignan solo al agregar o quitar, para que React no confunda las filas.
 */
function useStableKeys(length: number) {
  const counter = useRef(0);
  const keys = useRef<number[]>([]);
  while (keys.current.length < length) keys.current.push(counter.current++);
  if (keys.current.length > length) keys.current = keys.current.slice(0, length);

  return {
    at: (index: number) => keys.current[index] ?? index,
    append: () => keys.current.push(counter.current++),
    remove: (index: number) => {
      keys.current = keys.current.filter((_, i) => i !== index);
    },
  };
}
