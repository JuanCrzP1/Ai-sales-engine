import { useId, type ReactNode } from "react";
import type { FieldFeedback } from "./fieldFeedback";

export interface SegmentOption {
  value: string;
  label: string;
}

interface SegmentedControlProps {
  label: string;
  hint?: ReactNode;
  value: string;
  options: SegmentOption[];
  issue?: FieldFeedback;
  onChange: (value: string) => void;
}

/** Elegir una opción entre pocas (Sí / No, Fijo / Variable / Gratis) con un clic. Son botones de opción nativos: accesible por teclado. */
export function SegmentedControl({ label, hint, value, options, issue, onChange }: SegmentedControlProps) {
  const name = useId();
  return (
    <fieldset className="field segmented-field">
      <legend className="field__label">{label}</legend>
      {hint && <p className="field__hint">{hint}</p>}
      <div className="segmented">
        {options.map((option) => (
          <label key={option.value} className={`segmented__option${option.value === value ? " segmented__option--active" : ""}`}>
            <input type="radio" name={name} value={option.value} checked={option.value === value} onChange={() => onChange(option.value)} />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
      {issue && <p className={`field__message field__message--${issue.severity}`}>{issue.message}</p>}
    </fieldset>
  );
}
