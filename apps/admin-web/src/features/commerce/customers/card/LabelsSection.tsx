import { useState } from "react";
import { MAX_LABELS_PER_CUSTOMER, toggled, type Label, type LabelColor, type LabelRef } from "../../../../domain/commerce/labels";
import type { CardResult } from "../../../../state/useCustomerCard";
import { LabelChip } from "../labels/LabelChip";
import { NewLabelForm } from "../labels/NewLabelForm";

/**
 * Las etiquetas del cliente. «Cambiar» abre el catálogo: cada etiqueta se pone o se quita con un toque (se guarda de una vez), y ahí
 * mismo se crea una nueva, que queda puesta. `onManage` lleva a administrar el catálogo (renombrar, borrar).
 */
export function LabelsSection({
  own,
  catalog,
  saving,
  onSet,
  onCreate,
  onManage,
}: {
  own: LabelRef[];
  catalog: Label[];
  saving: boolean;
  onSet: (labelIds: string[]) => Promise<CardResult>;
  onCreate: (name: string, color: LabelColor, current: string[]) => Promise<CardResult>;
  onManage: () => void;
}) {
  const [picking, setPicking] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const selected = own.map((label) => label.id);
  const full = selected.length >= MAX_LABELS_PER_CUSTOMER;

  const toggle = async (labelId: string) => {
    const result = await onSet(toggled(selected, labelId));
    setProblem(result.ok ? null : result.message);
  };
  const create = async (name: string, color: LabelColor) => {
    const result = await onCreate(name, color, selected);
    return result.ok ? null : result.message;
  };

  return (
    <section className="card-section" aria-label="Etiquetas">
      <header className="card-section__head">
        <h3>Etiquetas</h3>
        <button type="button" className="link-button" aria-expanded={picking} onClick={() => setPicking(!picking)}>
          {picking ? "Listo" : own.length > 0 ? "Cambiar" : "Poner etiquetas"}
        </button>
      </header>
      {own.length === 0 && !picking && <p className="card-section__empty">Sin etiquetas.</p>}
      {own.length > 0 && !picking && (
        <div className="label-row">
          {own.map((label) => (
            <LabelChip key={label.id} label={label} />
          ))}
        </div>
      )}
      {picking && (
        <>
          {catalog.length > 0 && (
            <div className="label-row" role="group" aria-label="Elige sus etiquetas">
              {catalog.map((label) => {
                const on = selected.includes(label.id);
                return (
                  <button key={label.id} type="button" className={`label-chip label-chip--pick label-tone--${label.color}`} aria-pressed={on} disabled={saving || (!on && full)} onClick={() => void toggle(label.id)}>
                    {label.name}
                  </button>
                );
              })}
            </div>
          )}
          {problem && (
            <p className="field__message field__message--error" role="alert">
              {problem}
            </p>
          )}
          {full && <p className="card-section__empty">Ya tiene {MAX_LABELS_PER_CUSTOMER} etiquetas, el máximo: quita una para poner otra.</p>}
          {!full && <NewLabelForm existing={catalog} saving={saving} submitLabel="Crear y poner" onCreate={create} />}
          <button type="button" className="link-button" onClick={onManage}>
            Administrar etiquetas
          </button>
        </>
      )}
    </section>
  );
}
