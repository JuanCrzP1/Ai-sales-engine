import type { ReactNode } from "react";
import type { FieldFeedback } from "./fieldFeedback";

export interface ChoiceOption<T extends string = string> {
  value: T;
  label: string;
  hint?: string;
  badge?: ReactNode;
}

interface ChoiceGroupBaseProps<T extends string> {
  legend: string;
  hint?: ReactNode;
  options: ChoiceOption<T>[];
  issue?: FieldFeedback;
  name: string;
}

interface CheckboxGroupProps<T extends string> extends ChoiceGroupBaseProps<T> {
  values: T[];
  onChange: (values: T[]) => void;
}

/** Selección múltiple con tarjetas accesibles (casillas nativas). */
export function CheckboxGroup<T extends string>({ legend, hint, options, issue, name, values, onChange }: CheckboxGroupProps<T>) {
  const toggle = (value: T, checked: boolean) =>
    onChange(checked ? [...values, value] : values.filter((item) => item !== value));

  return (
    <ChoiceFieldset legend={legend} hint={hint} issue={issue}>
      {options.map((option) => (
        <label key={option.value} className="choice">
          <input
            type="checkbox"
            name={name}
            value={option.value}
            checked={values.includes(option.value)}
            onChange={(event) => toggle(option.value, event.target.checked)}
          />
          <ChoiceText option={option} />
        </label>
      ))}
    </ChoiceFieldset>
  );
}

interface RadioGroupProps<T extends string> extends ChoiceGroupBaseProps<T> {
  value: T;
  onChange: (value: T) => void;
}

/** Selección única con tarjetas accesibles (radios nativos). */
export function RadioGroup<T extends string>({ legend, hint, options, issue, name, value, onChange }: RadioGroupProps<T>) {
  return (
    <ChoiceFieldset legend={legend} hint={hint} issue={issue}>
      {options.map((option) => (
        <label key={option.value} className="choice">
          <input
            type="radio"
            name={name}
            value={option.value}
            checked={value === option.value}
            onChange={() => onChange(option.value)}
          />
          <ChoiceText option={option} />
        </label>
      ))}
    </ChoiceFieldset>
  );
}

function ChoiceFieldset({ legend, hint, issue, children }: { legend: string; hint?: ReactNode; issue?: FieldFeedback; children: ReactNode }) {
  return (
    <fieldset className="choice-group">
      <legend className="field__label">{legend}</legend>
      {hint && <p className="field__hint">{hint}</p>}
      <div className="choice-grid">{children}</div>
      {issue && (
        <p className={`field__message field__message--${issue.severity}`} role={issue.severity === "error" ? "alert" : undefined}>
          {issue.message}
        </p>
      )}
    </fieldset>
  );
}

function ChoiceText({ option }: { option: ChoiceOption }) {
  return (
    <span className="choice__text">
      <span className="choice__label">
        {option.label} {option.badge}
      </span>
      {option.hint && <span className="field__hint">{option.hint}</span>}
    </span>
  );
}
