import { useId, type ReactNode } from "react";
import { countWords } from "../../lib/text";
import type { FieldFeedback } from "./fieldFeedback";

export interface SelectOption<T extends string = string> {
  value: T;
  label: string;
}

interface FieldProps {
  label: string;
  hint?: ReactNode;
  required?: boolean;
  issue?: FieldFeedback;
  /** Atajo para un mensaje de error simple. */
  error?: string;
  footer?: ReactNode;
  children: (control: { id: string; describedBy: string | undefined; invalid: boolean }) => ReactNode;
}

/** Etiqueta, ayuda y mensaje de validación comunes a todos los controles. */
export function Field({ label, hint, required, issue: configIssue, error, footer, children }: FieldProps) {
  const id = useId();
  const issue = configIssue ?? (error ? { severity: "error" as const, message: error } : undefined);
  const hintId = hint ? `${id}-hint` : undefined;
  const messageId = issue ? `${id}-message` : undefined;
  const describedBy = [hintId, messageId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
        {required && (
          <span className="field__required" aria-hidden="true">
            *
          </span>
        )}
      </label>
      {children({ id, describedBy, invalid: issue?.severity === "error" })}
      {hint && (
        <p className="field__hint" id={hintId}>
          {hint}
        </p>
      )}
      {issue && (
        <p className={`field__message field__message--${issue.severity}`} id={messageId} role={issue.severity === "error" ? "alert" : undefined}>
          {issue.message}
        </p>
      )}
      {footer}
    </div>
  );
}

interface TextFieldProps extends Omit<FieldProps, "children" | "footer"> {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: "text" | "url" | "tel" | "email";
  wordLimit?: number;
  inputMode?: "text" | "numeric" | "tel" | "url" | "email";
  autoComplete?: string;
  /** Id de un <datalist> con sugerencias. */
  list?: string;
}

export function TextField({ value, onChange, placeholder, type = "text", wordLimit, inputMode, autoComplete, list, ...field }: TextFieldProps) {
  return (
    <Field {...field} footer={wordLimit ? <WordCounter text={value} limit={wordLimit} /> : undefined}>
      {({ id, describedBy, invalid }) => (
        <input
          id={id}
          className="input"
          type={type}
          value={value}
          placeholder={placeholder}
          inputMode={inputMode}
          list={list}
          autoComplete={autoComplete ?? "off"}
          required={field.required}
          aria-invalid={invalid || undefined}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
    </Field>
  );
}

interface TextAreaFieldProps extends Omit<FieldProps, "children" | "footer"> {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  wordLimit?: number;
}

export function TextAreaField({ value, onChange, placeholder, rows = 3, wordLimit, ...field }: TextAreaFieldProps) {
  return (
    <Field {...field} footer={wordLimit ? <WordCounter text={value} limit={wordLimit} /> : undefined}>
      {({ id, describedBy, invalid }) => (
        <textarea
          id={id}
          className="textarea"
          rows={rows}
          value={value}
          placeholder={placeholder}
          required={field.required}
          aria-invalid={invalid || undefined}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
    </Field>
  );
}

interface SelectFieldProps<T extends string> extends Omit<FieldProps, "children" | "footer"> {
  value: T;
  options: SelectOption<T>[];
  onChange: (value: T) => void;
}

export function SelectField<T extends string>({ value, options, onChange, ...field }: SelectFieldProps<T>) {
  return (
    <Field {...field}>
      {({ id, describedBy, invalid }) => (
        <select
          id={id}
          className="select"
          value={value}
          aria-invalid={invalid || undefined}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value as T)}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}
    </Field>
  );
}

interface NumberFieldProps extends Omit<FieldProps, "children" | "footer"> {
  value: number | null;
  onChange: (value: number | null) => void;
  placeholder?: string;
}

export function NumberField({ value, onChange, placeholder, ...field }: NumberFieldProps) {
  return (
    <Field {...field}>
      {({ id, describedBy, invalid }) => (
        <input
          id={id}
          className="input"
          type="number"
          min={0}
          step="any"
          inputMode="decimal"
          value={value ?? ""}
          placeholder={placeholder}
          required={field.required}
          aria-invalid={invalid || undefined}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value === "" ? null : Number(event.target.value))}
        />
      )}
    </Field>
  );
}

function WordCounter({ text, limit }: { text: string; limit: number }) {
  const words = countWords(text);
  const over = words > limit;
  return (
    <p className={`field__counter${over ? " field__counter--over" : ""}`} aria-live="polite">
      {words} / {limit} palabras
    </p>
  );
}
