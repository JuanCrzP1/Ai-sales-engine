import { useEffect, useId, useRef } from "react";
import { storedFieldHint } from "../../components/config/storedFieldHint";
import { Button } from "../../components/ui/Button";
import { NumberField, SelectField, TextAreaField, TextField } from "../../components/ui/FormFields";
import { ListEditor } from "../../components/ui/ListEditor";
import { Toggle } from "../../components/ui/Toggle";
import { BILLING_TYPES, CURRENCIES } from "../../domain/config/options";
import type { Offering, SalesMode } from "../../domain/config/types";
import { issuesFor } from "../../domain/validation/issues";
import type { ValidationIssue } from "../../domain/validation/types";

interface OfferingEditorProps {
  draft: Offering;
  isNew: boolean;
  issues: ValidationIssue[];
  salesMode: SalesMode;
  categorySuggestions: string[];
  onChange: (patch: Partial<Offering>) => void;
  onSave: () => void;
  onCancel: () => void;
}

export function OfferingEditor({ draft, isNew, issues, salesMode, categorySuggestions, onChange, onSave, onCancel }: OfferingEditorProps) {
  const isCatalog = salesMode === "catalog";
  const titleId = useId();
  const listId = useId();
  const containerRef = useRef<HTMLFormElement>(null);
  const issue = (field: string) => issuesFor(issues, `offerings.${draft.id}.${field}`)[0];

  useEffect(() => {
    containerRef.current?.querySelector<HTMLInputElement>("input")?.focus();
  }, [draft.id]);

  return (
    <form
      ref={containerRef}
      className="card"
      aria-labelledby={titleId}
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        onSave();
      }}
    >
      <h2 className="card__title" id={titleId}>
        {isNew ? (isCatalog ? "Nuevo producto" : "Nuevo plan o servicio") : `Editar: ${draft.name || "sin nombre"}`}
      </h2>

      <div className="grid-2">
        <TextField
          label="Nombre"
          required
          value={draft.name}
          onChange={(name) => onChange({ name })}
          issue={issue("name")}
          hint={storedFieldHint("offering.name", salesMode)}
        />
        {isCatalog && (
          <>
            <TextField
              label="Categoría"
              required
              value={draft.category}
              onChange={(category) => onChange({ category })}
              placeholder="Ej.: Bebidas"
              list={listId}
              issue={issue("category")}
              hint="El asistente menciona hasta cuatro categorías."
            />
            <datalist id={listId}>
              {categorySuggestions.map((category) => (
                <option key={category} value={category} />
              ))}
            </datalist>
          </>
        )}
      </div>

      <TextAreaField
        label="Descripción"
        value={draft.description}
        onChange={(description) => onChange({ description })}
        rows={2}
        hint={storedFieldHint("offering.description", salesMode)}
      />

      <div className="grid-2">
        <NumberField
          label={isCatalog || draft.billing === "one_time" ? "Precio" : "Precio mensual"}
          required
          value={draft.price}
          onChange={(price) => onChange({ price })}
          issue={issue("price")}
          hint={storedFieldHint("offering.price", salesMode)}
        />
        <SelectField label="Moneda" value={draft.currency} options={CURRENCIES} onChange={(currency) => onChange({ currency })} />
        {!isCatalog && (
          <>
            <SelectField label="Tipo de cobro" value={draft.billing} options={BILLING_TYPES} onChange={(billing) => onChange({ billing })} />
            <NumberField
              label="Costo inicial (opcional)"
              value={draft.setupFee}
              onChange={(setupFee) => onChange({ setupFee })}
              issue={issue("setupFee")}
              hint="Instalación, implementación o inscripción."
            />
          </>
        )}
      </div>

      <ListEditor
        label={isCatalog ? "Características relevantes" : "Qué incluye"}
        items={draft.features}
        onChange={(features) => onChange({ features })}
        placeholder={isCatalog ? "Ej.: Tamaño 12 oz" : "Ej.: Soporte por WhatsApp"}
        addLabel={isCatalog ? "Agregar característica" : "Agregar a lo que incluye"}
        hint={storedFieldHint("offering.features", salesMode)}
      />

      {!isCatalog && (
        <ListEditor
          label="Qué no incluye"
          items={draft.notIncluded}
          onChange={(notIncluded) => onChange({ notIncluded })}
          placeholder="Ej.: Publicidad pagada"
          addLabel="Agregar a lo que no incluye"
          hint="Ayuda al asistente a no prometer de más."
        />
      )}

      <Toggle
        label="Disponible para la venta"
        description="Si lo desactivas, el asistente no lo ofrecerá."
        checked={draft.available}
        onChange={(available) => onChange({ available })}
      />

      <div className="dialog__actions">
        <Button variant="ghost" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit">{isNew ? (isCatalog ? "Guardar producto" : "Guardar plan o servicio") : "Guardar cambios"}</Button>
      </div>
    </form>
  );
}
