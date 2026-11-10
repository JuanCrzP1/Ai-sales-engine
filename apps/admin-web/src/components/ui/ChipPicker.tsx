import { useState, type ReactNode } from "react";
import { Button } from "./Button";

interface ChipPickerProps {
  label: string;
  hint?: ReactNode;
  /** Opciones conocidas, en su orden natural: identificador → cómo se dice. */
  options: Record<string, string>;
  values: string[];
  /** Si se pueden agregar valores propios, además de los conocidos. */
  allowCustom?: boolean;
  onChange: (values: string[]) => void;
}

const slug = (text: string) =>
  text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");

/**
 * Elegir varias opciones con etiquetas en español en lugar de escribir identificadores (`detect_pain`). Lo elegido conserva el orden
 * natural de las opciones; los valores propios del negocio se muestran al final y se pueden quitar.
 */
export function ChipPicker({ label, hint, options, values, allowCustom = true, onChange }: ChipPickerProps) {
  const [draft, setDraft] = useState("");
  const known = Object.keys(options);
  const custom = values.filter((value) => !known.includes(value));
  const toggle = (value: string) => {
    const selected = values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
    onChange([...known.filter((key) => selected.includes(key)), ...selected.filter((item) => !known.includes(item))]);
  };
  const add = () => {
    const value = slug(draft);
    if (value && !values.includes(value)) onChange([...values, value]);
    setDraft("");
  };

  return (
    <fieldset className="field chip-picker">
      <legend className="field__label">{label}</legend>
      {hint && <p className="field__hint">{hint}</p>}
      <div className="chip-picker__chips">
        {known.map((key) => (
          <button key={key} type="button" className={`chip${values.includes(key) ? " chip--active" : ""}`} aria-pressed={values.includes(key)} onClick={() => toggle(key)}>
            {options[key]}
          </button>
        ))}
        {custom.map((value) => (
          <button key={value} type="button" className="chip chip--active chip--custom" aria-pressed="true" onClick={() => toggle(value)} title="Quitar">
            {value.replace(/_/g, " ")} ✕
          </button>
        ))}
      </div>
      {allowCustom && (
        <div className="chip-picker__add">
          <input
            className="input"
            value={draft}
            placeholder="Otro (escríbelo y agrégalo)"
            aria-label={`Agregar otro a ${label.toLowerCase()}`}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                add();
              }
            }}
          />
          <Button variant="secondary" size="small" onClick={add} disabled={!slug(draft)}>
            Agregar
          </Button>
        </div>
      )}
    </fieldset>
  );
}
