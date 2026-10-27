import { useState } from "react";
import { Field } from "./FormFields";
import { Icon } from "./Icon";

interface PasswordFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  autoComplete: "current-password" | "new-password";
  error?: string;
  hint?: string;
  required?: boolean;
}

/** Campo de contraseña con botón para mostrarla u ocultarla. */
export function PasswordField({ label, value, onChange, autoComplete, error, hint, required = true }: PasswordFieldProps) {
  const [visible, setVisible] = useState(false);

  return (
    <Field label={label} error={error} hint={hint} required={required}>
      {({ id, describedBy, invalid }) => (
        <span className="input-group">
          <input
            id={id}
            className="input"
            type={visible ? "text" : "password"}
            value={value}
            autoComplete={autoComplete}
            required={required}
            aria-invalid={invalid || undefined}
            aria-describedby={describedBy}
            onChange={(event) => onChange(event.target.value)}
          />
          <button
            type="button"
            className="input-group__action"
            aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
            aria-pressed={visible}
            onClick={() => setVisible((current) => !current)}
          >
            <Icon name={visible ? "eyeOff" : "eye"} size={18} />
          </button>
        </span>
      )}
    </Field>
  );
}
