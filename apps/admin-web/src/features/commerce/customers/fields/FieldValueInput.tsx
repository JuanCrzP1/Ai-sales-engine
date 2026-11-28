import { SelectField, TextField } from "../../../../components/ui/FormFields";
import { MAX_TEXT_VALUE, type CustomerField } from "../../../../domain/commerce/customerFields";

/**
 * El control para llenar un campo, según su tipo: texto, número (se escribe como en Colombia: «1.500.000» o «1,5»), fecha con su
 * calendario, sí o no, o una de las opciones de la lista. Vacío ("") deja el campo vacío.
 */
export function FieldValueInput({ field, value, error, onChange }: { field: CustomerField; value: string; error?: string; onChange: (value: string) => void }) {
  switch (field.kind) {
    case "number":
      return <TextField label={field.name} value={value} onChange={onChange} inputMode="decimal" placeholder="Ej.: 1.500.000" error={error} />;
    case "date":
      return <TextField label={field.name} type="date" value={value} onChange={onChange} error={error} />;
    case "yes_no":
      return (
        <SelectField
          label={field.name}
          value={value}
          options={[
            { value: "", label: "Sin definir" },
            { value: "true", label: "Sí" },
            { value: "false", label: "No" },
          ]}
          onChange={onChange}
          error={error}
        />
      );
    case "choice":
      return (
        <SelectField
          label={field.name}
          value={value}
          options={[{ value: "", label: "Sin elegir" }, ...field.options.map((option) => ({ value: option, label: option }))]}
          onChange={onChange}
          error={error}
        />
      );
    default:
      return <TextField label={field.name} value={value} onChange={onChange} maxLength={MAX_TEXT_VALUE} error={error} />;
  }
}
