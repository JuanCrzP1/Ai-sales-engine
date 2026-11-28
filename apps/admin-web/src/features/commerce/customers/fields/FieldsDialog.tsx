import { useState, type FormEvent } from "react";
import { Button } from "../../../../components/ui/Button";
import { Dialog } from "../../../../components/ui/Dialog";
import { TextAreaField, TextField } from "../../../../components/ui/FormFields";
import {
  FIELD_KIND_LABELS,
  MAX_FIELDS,
  MAX_FIELD_NAME,
  fieldNameProblem,
  optionsFromText,
  optionsProblem,
  removedOptions,
  type CustomerField,
  type FieldChange,
} from "../../../../domain/commerce/customerFields";
import { useCommerce } from "../../../../state/commerceContext";
import { persistenceErrorMessage } from "../../../../state/directoryContext";
import { NewFieldForm } from "./NewFieldForm";

const filledText = (count: number) => (count === 0 ? "Nadie lo tiene lleno" : `${count} ${count === 1 ? "cliente lo tiene" : "clientes lo tienen"}`);

interface Editing {
  id: string;
  name: string;
  options: string;
  problem: { on: "name" | "options"; message: string } | null;
}

/**
 * Los campos del cliente del negocio: crear, cambiar el nombre y las opciones de una lista, y borrar, viendo cuántos clientes tienen
 * lleno cada uno. Es de quien configura el negocio: afecta a todos sus clientes. Antes de guardar avisa qué opciones se quitan (quien
 * las tenía queda sin valor) y antes de borrar, en cuántos clientes se borra el dato. Cada cambio avisa con `onChanged`.
 */
export function FieldsDialog({ fields, onChanged, onClose }: { fields: CustomerField[]; onChanged: () => void; onClose: () => void }) {
  const commerce = useCommerce();
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<Editing | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  /** Hace un cambio y devuelve el mensaje si falló, o null. */
  const run = async (work: () => Promise<unknown>): Promise<string | null> => {
    setSaving(true);
    try {
      await work();
      onChanged();
      return null;
    } catch (error) {
      return persistenceErrorMessage(error);
    } finally {
      setSaving(false);
    }
  };
  const save = async (field: CustomerField, event: FormEvent) => {
    event.preventDefault();
    if (!editing) return;
    const named = fieldNameProblem(editing.name, fields, field.id);
    if (named) return setEditing({ ...editing, problem: { on: "name", message: named } });
    const change: FieldChange = {};
    if (editing.name.trim() !== field.name) change.name = editing.name.trim();
    if (field.kind === "choice") {
      const options = optionsFromText(editing.options);
      const listed = optionsProblem(options);
      if (listed) return setEditing({ ...editing, problem: { on: "options", message: listed } });
      if (options.join("\n") !== field.options.join("\n")) change.options = options;
    }
    if (Object.keys(change).length === 0) return setEditing(null);
    const failed = await run(() => commerce.updateCustomerField(field.id, change));
    setEditing(failed ? { ...editing, problem: { on: "name", message: failed } } : null);
  };
  const remove = async (field: CustomerField) => {
    setProblem(await run(() => commerce.deleteCustomerField(field.id)));
    setDeleting(null);
  };

  return (
    <Dialog title="Campos del cliente" description="Los datos propios que guardas de cada cliente. Tu equipo los llena desde su ficha." onClose={onClose}>
      <div className="labels-dialog">
        {fields.length < MAX_FIELDS ? (
          <NewFieldForm existing={fields} saving={saving} onCreate={(input) => run(() => commerce.createCustomerField(input))} />
        ) : (
          <p className="card-section__empty">Ya tienes {MAX_FIELDS} campos, el máximo: borra alguno para crear otro.</p>
        )}
        {problem && (
          <p className="field__message field__message--error" role="alert">
            {problem}
          </p>
        )}
        {fields.length === 0 ? (
          <p className="card-section__empty">Todavía no tienes campos. Crea el primero arriba.</p>
        ) : (
          <ul className="labels-list" aria-label="Tus campos">
            {fields.map((field) => {
              const removed = editing?.id === field.id && field.kind === "choice" ? removedOptions(field.options, optionsFromText(editing.options)) : [];
              return (
                <li key={field.id} className="labels-list__item" aria-label={field.name}>
                  {editing?.id === field.id ? (
                    <form className="labels-list__rename" aria-label={`Editar ${field.name}`} noValidate onSubmit={(event) => void save(field, event)}>
                      <TextField
                        label="Nombre"
                        value={editing.name}
                        onChange={(name) => setEditing({ ...editing, name })}
                        maxLength={MAX_FIELD_NAME}
                        error={editing.problem?.on === "name" ? editing.problem.message : undefined}
                      />
                      {field.kind === "choice" && (
                        <TextAreaField
                          label="Opciones"
                          hint="Una por línea."
                          rows={4}
                          value={editing.options}
                          onChange={(options) => setEditing({ ...editing, options })}
                          error={editing.problem?.on === "options" ? editing.problem.message : undefined}
                        />
                      )}
                      {removed.length > 0 && (
                        <p className="field-form__warning" role="status">
                          Se quita {removed.map((option) => `«${option}»`).join(", ")}: los clientes que la tienen quedan sin valor en este campo.
                        </p>
                      )}
                      <div className="button-row">
                        <Button type="submit" size="small" disabled={saving}>
                          Guardar
                        </Button>
                        <Button size="small" variant="ghost" disabled={saving} onClick={() => setEditing(null)}>
                          Cancelar
                        </Button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <span className="labels-list__main field-item">
                        <strong>{field.name}</strong>
                        <span className="labels-list__count">
                          {FIELD_KIND_LABELS[field.kind]}
                          {field.kind === "choice" ? `: ${field.options.join(", ")}` : ""} · {filledText(field.filled)}
                        </span>
                      </span>
                      <span className="labels-list__actions">
                        {deleting === field.id ? (
                          <>
                            <span className="labels-list__count">{field.filled > 0 ? `Se borra este dato en ${field.filled} ${field.filled === 1 ? "cliente" : "clientes"}.` : "¿Borrarlo?"}</span>
                            <button type="button" className="link-button link-button--danger" disabled={saving} onClick={() => void remove(field)}>
                              Sí, borrar
                            </button>
                            <button type="button" className="link-button" onClick={() => setDeleting(null)}>
                              No
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              className="link-button"
                              aria-label={`Editar el campo ${field.name}`}
                              onClick={() => setEditing({ id: field.id, name: field.name, options: field.options.join("\n"), problem: null })}
                            >
                              Editar
                            </button>
                            <button type="button" className="link-button" aria-label={`Borrar el campo ${field.name}`} onClick={() => setDeleting(field.id)}>
                              Borrar
                            </button>
                          </>
                        )}
                      </span>
                    </>
                  )}
                </li>
              );
            })}
          </ul>
        )}
        <p className="card-section__empty">El tipo de dato no cambia después de crear el campo.</p>
      </div>
    </Dialog>
  );
}
