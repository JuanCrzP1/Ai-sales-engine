import { emptyValue, fieldHint, fieldLabel, fieldShape, valueLabel, type ContractSchema, type SchemaNode } from "../../domain/config/contractSchema";
import { Button } from "../ui/Button";
import { CheckboxGroup } from "../ui/ChoiceGroup";
import { ConfirmButton } from "../ui/ConfirmButton";
import type { FieldFeedback } from "../ui/fieldFeedback";
import { NumberField, SelectField, TextAreaField, TextField } from "../ui/FormFields";
import { ListEditor } from "../ui/ListEditor";
import { Toggle } from "../ui/Toggle";

interface ContractFieldProps {
  root: ContractSchema;
  name: string;
  node: SchemaNode;
  value: unknown;
  /** Ruta en el documento (`sales.objections.0.topic`): la misma que usan los errores del servidor. */
  path: string;
  /** Si el contrato lo exige dentro de su objeto. */
  required?: boolean;
  /** Muestra solo los campos del objeto, sin título ni opción de quitarlo. */
  bare?: boolean;
  issueAt: (path: string) => FieldFeedback | undefined;
  onChange: (value: unknown) => void;
}

/** Un campo del contrato, según lo que dice su esquema. Es recursivo: objetos y listas contienen más campos. */
export function ContractField({ root, name, node, value, path, required = false, bare = false, issueAt, onChange }: ContractFieldProps) {
  const shape = fieldShape(root, node);
  const label = fieldLabel(name, shape.node);
  const hint = fieldHint(name, shape.node);
  const issue = issueAt(path);
  const optional = shape.nullable || !required;

  switch (shape.kind) {
    case "text":
    case "date": {
      const type = shape.kind === "date" ? "date" : "text";
      return (
        <TextField
          label={label}
          hint={hint}
          required={required}
          type={type}
          value={(value as string | number | null | undefined)?.toString() ?? ""}
          issue={issue}
          onChange={(text) => onChange(shape.nullable && !text.trim() ? null : text)}
        />
      );
    }
    case "longText":
      return (
        <TextAreaField
          label={label}
          hint={hint}
          required={required}
          value={(value as string | null | undefined) ?? ""}
          issue={issue}
          onChange={(text) => onChange(shape.nullable && !text.trim() ? null : text)}
        />
      );
    case "number":
      return <NumberField label={label} hint={hint} required={required} value={(value as number | null | undefined) ?? null} issue={issue} onChange={onChange} />;
    case "boolean":
      if (!shape.nullable) return <Toggle label={label} description={hint} checked={value === true} onChange={onChange} />;
      return (
        <SelectField
          label={label}
          hint={hint}
          value={value === true ? "yes" : value === false ? "no" : ""}
          options={[
            { value: "", label: "Sin indicar" },
            { value: "yes", label: "Sí" },
            { value: "no", label: "No" },
          ]}
          issue={issue}
          onChange={(choice) => onChange(choice === "" ? null : choice === "yes")}
        />
      );
    case "choice": {
      const options = (shape.node.enum ?? []).map((option) => ({ value: option, label: valueLabel(option) }));
      return (
        <SelectField
          label={label}
          hint={hint}
          value={(value as string | null | undefined) ?? ""}
          options={optional ? [{ value: "", label: "Sin indicar" }, ...options] : options}
          issue={issue}
          onChange={(choice) => onChange(choice === "" ? null : choice)}
        />
      );
    }
    case "list":
      return (
        <div className="contract-list">
          <ListEditor label={label} hint={hint} items={(value as string[] | null | undefined) ?? []} onChange={(items) => onChange(shape.nullable && items.length === 0 ? null : items)} />
          {issue && <p className={`field__message field__message--${issue.severity}`}>{issue.message}</p>}
        </div>
      );
    case "choiceList": {
      const options = (fieldShape(root, shape.node.items ?? {}).node.enum ?? []).map((option) => ({ value: option, label: valueLabel(option) }));
      return <CheckboxGroup legend={label} hint={hint} name={path} options={options} values={(value as string[] | null | undefined) ?? []} issue={issue} onChange={onChange} />;
    }
    case "objectList": {
      const items = (value as unknown[] | null | undefined) ?? [];
      const itemNode = shape.node.items ?? {};
      const change = (next: unknown[]) => onChange(shape.nullable && next.length === 0 ? null : next);
      return (
        <fieldset className="contract-group">
          <legend className="field__label">{label}</legend>
          {hint && <p className="field__hint">{hint}</p>}
          {issue && <p className={`field__message field__message--${issue.severity}`}>{issue.message}</p>}
          {items.map((item, index) => (
            <div className="subcard" key={index}>
              <div className="card__header">
                <h3 className="field__label">
                  {label}: {index + 1}
                </h3>
                <ConfirmButton confirmLabel="Sí, quitar" onConfirm={() => change(items.filter((_, position) => position !== index))}>
                  Quitar
                </ConfirmButton>
              </div>
              <ObjectFields
                root={root}
                node={itemNode}
                value={item as Record<string, unknown>}
                path={`${path}.${index}`}
                issueAt={issueAt}
                onChange={(next) => change(items.map((current, position) => (position === index ? next : current)))}
              />
            </div>
          ))}
          <div>
            <Button variant="secondary" size="small" onClick={() => change([...items, emptyValue(root, itemNode)])}>
              Agregar a {label.toLowerCase()}
            </Button>
          </div>
        </fieldset>
      );
    }
    case "object": {
      const current = value as Record<string, unknown> | null | undefined;
      if (bare) return <ObjectFields root={root} node={node} value={current ?? {}} path={path} issueAt={issueAt} onChange={onChange} />;
      if (!current) {
        return (
          <div className="contract-group">
            <p className="field__label">{label}</p>
            {hint && <p className="field__hint">{hint}</p>}
            <div>
              <Button variant="secondary" size="small" onClick={() => onChange(emptyValue(root, node))}>
                Agregar: {label.toLowerCase()}
              </Button>
            </div>
          </div>
        );
      }
      return (
        <fieldset className="contract-group subcard">
          <legend className="field__label">{label}</legend>
          {hint && <p className="field__hint">{hint}</p>}
          {issue && <p className={`field__message field__message--${issue.severity}`}>{issue.message}</p>}
          <ObjectFields root={root} node={node} value={current} path={path} issueAt={issueAt} onChange={onChange} />
          {optional && (
            <div>
              <ConfirmButton confirmLabel="Sí, quitar" onConfirm={() => onChange(null)}>
                Quitar: {label.toLowerCase()}
              </ConfirmButton>
            </div>
          )}
        </fieldset>
      );
    }
    case "keyedLists": {
      const current = (value as Record<string, string[]> | null | undefined) ?? {};
      const keys = shape.node.propertyNames?.enum ?? [];
      return (
        <fieldset className="contract-group">
          <legend className="field__label">{label}</legend>
          {keys.map((key) => (
            <ListEditor
              key={key}
              label={fieldLabel(key, {})}
              items={current[key] ?? []}
              onChange={(items) => {
                const next = { ...current };
                if (items.length > 0) next[key] = items;
                else delete next[key];
                onChange(Object.keys(next).length > 0 ? next : null);
              }}
            />
          ))}
        </fieldset>
      );
    }
    case "pairs":
      return <PairsField label={label} hint={hint} value={(value as Record<string, string | number> | undefined) ?? {}} onChange={onChange} />;
  }
}

function ObjectFields({
  root,
  node,
  value,
  path,
  issueAt,
  onChange,
}: {
  root: ContractSchema;
  node: SchemaNode;
  value: Record<string, unknown>;
  path: string;
  issueAt: (path: string) => FieldFeedback | undefined;
  onChange: (value: Record<string, unknown>) => void;
}) {
  const shape = fieldShape(root, node).node;
  return (
    <>
      {Object.entries(shape.properties ?? {}).map(([key, property]) => (
        <ContractField
          key={key}
          root={root}
          name={key}
          node={property}
          value={value[key]}
          path={`${path}.${key}`}
          required={(shape.required ?? []).includes(key)}
          issueAt={issueAt}
          onChange={(next) => onChange({ ...value, [key]: next })}
        />
      ))}
    </>
  );
}

/** Pares nombre y valor de un objeto abierto (talla: M, color: rojo). */
function PairsField({ label, hint, value, onChange }: { label: string; hint?: string; value: Record<string, string | number>; onChange: (value: Record<string, string | number>) => void }) {
  const pairs = Object.entries(value);
  const replace = (index: number, pair: [string, string | number] | null) => onChange(Object.fromEntries(pair ? pairs.map((current, position) => (position === index ? pair : current)) : pairs.filter((_, position) => position !== index)));
  return (
    <fieldset className="contract-group">
      <legend className="field__label">{label}</legend>
      {hint && <p className="field__hint">{hint}</p>}
      {pairs.map(([key, item], index) => (
        <div className="grid-2" key={index}>
          <TextField label="Nombre" value={key} onChange={(text) => replace(index, [text, item])} />
          <TextField label="Valor" value={String(item)} onChange={(text) => replace(index, [key, text])} />
          <div>
            <Button variant="danger" size="small" onClick={() => replace(index, null)}>
              Quitar
            </Button>
          </div>
        </div>
      ))}
      <div>
        <Button variant="secondary" size="small" onClick={() => onChange({ ...value, [`dato_${pairs.length + 1}`]: "" })}>
          Agregar a {label.toLowerCase()}
        </Button>
      </div>
    </fieldset>
  );
}
