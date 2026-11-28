import { useState, type FormEvent } from "react";
import { Button } from "../../../../components/ui/Button";
import { inputValue, valueText, type FieldRawValue, type FieldValue } from "../../../../domain/commerce/customerFields";
import { relativeTime } from "../../../../domain/inbox/format";
import type { CardResult } from "../../../../state/useCustomerCard";
import { FieldValueInput } from "../fields/FieldValueInput";

/**
 * Los datos propios del cliente: un renglón por cada campo del negocio, con su valor y quién lo puso. «Editar» los vuelve
 * controles y «Guardar» manda solo los que cambiaron (todos o ninguno). Sin campos todavía, quien configura el negocio los crea
 * (`onManage`); los demás saben a quién pedírselo.
 */
export function FieldsSection({
  fields,
  saving,
  canManage,
  onSave,
  onManage,
}: {
  fields: FieldValue[];
  saving: boolean;
  canManage: boolean;
  onSave: (values: Record<string, FieldRawValue>) => Promise<CardResult>;
  onManage: () => void;
}) {
  const [draft, setDraft] = useState<Record<string, string> | null>(null);
  const [problem, setProblem] = useState<{ fieldId: string | null; message: string } | null>(null);

  const edit = () => {
    setDraft(Object.fromEntries(fields.map((item) => [item.field.id, inputValue(item.field.kind, item.value)])));
    setProblem(null);
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!draft) return;
    const changed = Object.fromEntries(
      fields
        .filter((item) => (draft[item.field.id] ?? "") !== inputValue(item.field.kind, item.value))
        .map((item) => [item.field.id, draft[item.field.id]?.trim() ? draft[item.field.id]! : null]),
    );
    if (Object.keys(changed).length === 0) return setDraft(null);
    const result = await onSave(changed);
    if (result.ok) {
      setDraft(null);
      setProblem(null);
    } else {
      setProblem({ fieldId: result.field && result.field in changed ? result.field : null, message: result.message });
    }
  };

  return (
    <section className="card-section" aria-label="Datos del cliente">
      <header className="card-section__head">
        <h3>Datos del cliente</h3>
        {fields.length > 0 && !draft && (
          <button type="button" className="link-button" onClick={edit}>
            Editar
          </button>
        )}
      </header>

      {fields.length === 0 &&
        (canManage ? (
          <div className="card-section__actions">
            <p className="card-section__empty">Guarda datos propios de cada cliente, como su ciudad, su cumpleaños o qué tipo de cliente es.</p>
            <button type="button" className="link-button" onClick={onManage}>
              Crear campos
            </button>
          </div>
        ) : (
          <p className="card-section__empty">Tu negocio aún no tiene campos. El dueño o un administrador los crea en Clientes → Campos.</p>
        ))}

      {fields.length > 0 && !draft && (
        <dl className="field-values">
          {fields.map((item) => {
            const text = valueText(item.field.kind, item.value);
            return (
              <div key={item.field.id} className="field-values__row">
                <dt>{item.field.name}</dt>
                <dd>
                  <span className={text ? undefined : "field-values__empty"}>{text ?? "—"}</span>
                  {text && item.updatedBy && item.updatedAt && (
                    <small>
                      {item.updatedBy} · {relativeTime(item.updatedAt)}
                    </small>
                  )}
                </dd>
              </div>
            );
          })}
        </dl>
      )}

      {draft && (
        <form className="field-values__form" aria-label="Editar los datos del cliente" noValidate onSubmit={submit}>
          {fields.map((item) => (
            <FieldValueInput
              key={item.field.id}
              field={item.field}
              value={draft[item.field.id] ?? ""}
              error={problem?.fieldId === item.field.id ? problem.message : undefined}
              onChange={(value) => setDraft({ ...draft, [item.field.id]: value })}
            />
          ))}
          {problem && problem.fieldId === null && (
            <p className="field__message field__message--error" role="alert">
              {problem.message}
            </p>
          )}
          <div className="button-row">
            <Button type="submit" size="small" disabled={saving}>
              {saving ? "Guardando…" : "Guardar"}
            </Button>
            <Button size="small" variant="ghost" disabled={saving} onClick={() => setDraft(null)}>
              Cancelar
            </Button>
          </div>
          {canManage && (
            <button type="button" className="link-button" onClick={onManage}>
              Administrar campos
            </button>
          )}
        </form>
      )}
    </section>
  );
}
