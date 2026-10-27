import { useId, type ReactNode } from "react";

interface ToggleProps {
  label: string;
  description?: ReactNode;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

/** Interruptor accesible basado en una casilla nativa con rol "switch". */
export function Toggle({ label, description, checked, onChange }: ToggleProps) {
  const descriptionId = useId();
  return (
    <label className="toggle">
      <input
        type="checkbox"
        role="switch"
        className="toggle__input"
        checked={checked}
        aria-describedby={description ? descriptionId : undefined}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span className="toggle__text">
        <span className="toggle__label">{label}</span>
        {description && (
          <span className="field__hint" id={descriptionId}>
            {description}
          </span>
        )}
      </span>
    </label>
  );
}
