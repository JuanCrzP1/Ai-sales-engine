import { useState, type FormEvent } from "react";
import { Button } from "../../../../components/ui/Button";
import { SelectField, TextAreaField, TextField } from "../../../../components/ui/FormFields";
import {
  FIELD_KINDS,
  FIELD_KIND_HINTS,
  FIELD_KIND_LABELS,
  MAX_FIELD_NAME,
  fieldNameProblem,
  optionsFromText,
  optionsProblem,
  type CustomerField,
  type FieldKind,
  type NewFieldInput,
} from "../../../../domain/commerce/customerFields";

/**
 * Crear un campo: su nombre, su tipo y, si es una lista, sus opciones (una por línea). Avisa antes de guardar si ya hay uno que se
 * lee igual o si las opciones no sirven. `onCreate` devuelve el mensaje del servidor si no se pudo, o null si quedó creado.
 */
export function NewFieldForm({ existing, saving, onCreate }: { existing: CustomerField[]; saving: boolean; onCreate: (input: NewFieldInput) => Promise<string | null> }) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState<FieldKind>("text");
  const [options, setOptions] = useState("");
  const [problem, setProblem] = useState<{ on: "name" | "options"; message: string } | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const list = optionsFromText(options);
    const named = fieldNameProblem(name, existing);
    if (named) return setProblem({ on: "name", message: named });
    const listed = kind === "choice" ? optionsProblem(list) : null;
    if (listed) return setProblem({ on: "options", message: listed });
    const failed = await onCreate({ name: name.trim(), kind, ...(kind === "choice" ? { options: list } : {}) });
    setProblem(failed ? { on: "name", message: failed } : null);
    if (!failed) {
      setName("");
      setKind("text");
      setOptions("");
    }
  };

  return (
    <form className="field-form" aria-label="Campo nuevo" noValidate onSubmit={submit}>
      <div className="field-form__row">
        <TextField label="Nombre del campo" value={name} onChange={setName} maxLength={MAX_FIELD_NAME} placeholder="Ej.: Ciudad" error={problem?.on === "name" ? problem.message : undefined} />
        <SelectField
          label="Tipo de dato"
          value={kind}
          options={FIELD_KINDS.map((item) => ({ value: item, label: FIELD_KIND_LABELS[item] }))}
          onChange={(value) => setKind(value as FieldKind)}
          hint={FIELD_KIND_HINTS[kind]}
        />
      </div>
      {kind === "choice" && (
        <TextAreaField
          label="Opciones"
          hint="Una por línea."
          rows={4}
          value={options}
          onChange={setOptions}
          placeholder={"Mayorista\nAl detal\nDistribuidor"}
          error={problem?.on === "options" ? problem.message : undefined}
        />
      )}
      <div className="button-row">
        <Button type="submit" size="small" variant="secondary" disabled={saving}>
          Crear campo
        </Button>
      </div>
    </form>
  );
}
