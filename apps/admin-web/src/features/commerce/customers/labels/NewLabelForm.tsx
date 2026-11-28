import { useState, type FormEvent } from "react";
import { Button } from "../../../../components/ui/Button";
import { TextField } from "../../../../components/ui/FormFields";
import { DEFAULT_LABEL_COLOR, MAX_LABEL_NAME, nameProblem, type LabelColor, type LabelRef } from "../../../../domain/commerce/labels";
import { LabelColorPicker } from "./LabelColorPicker";

/**
 * Crear una etiqueta: su nombre y su color. Avisa antes de guardar si ya hay una que se lee igual. `onCreate` devuelve el mensaje
 * del servidor si no se pudo, o null si quedó creada (y el formulario se limpia).
 */
export function NewLabelForm({ existing, saving, submitLabel = "Crear etiqueta", onCreate }: { existing: LabelRef[]; saving: boolean; submitLabel?: string; onCreate: (name: string, color: LabelColor) => Promise<string | null> }) {
  const [name, setName] = useState("");
  const [color, setColor] = useState<LabelColor>(DEFAULT_LABEL_COLOR);
  const [problem, setProblem] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const found = nameProblem(name, existing) ?? (await onCreate(name.trim(), color));
    setProblem(found);
    if (!found) {
      setName("");
      setColor(DEFAULT_LABEL_COLOR);
    }
  };

  return (
    <form className="label-form" aria-label="Nueva etiqueta" noValidate onSubmit={submit}>
      <TextField label="Etiqueta nueva" value={name} onChange={setName} maxLength={MAX_LABEL_NAME} placeholder="Ej.: Mayorista" error={problem ?? undefined} />
      <div className="label-form__row">
        <LabelColorPicker value={color} disabled={saving} onChange={setColor} />
        <Button type="submit" size="small" variant="secondary" disabled={saving}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
