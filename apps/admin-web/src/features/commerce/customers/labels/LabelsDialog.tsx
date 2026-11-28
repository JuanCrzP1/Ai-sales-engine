import { useState } from "react";
import { Button } from "../../../../components/ui/Button";
import { Dialog } from "../../../../components/ui/Dialog";
import { TextField } from "../../../../components/ui/FormFields";
import { MAX_LABEL_NAME, nameProblem, type Label, type LabelColor } from "../../../../domain/commerce/labels";
import { useCommerce } from "../../../../state/commerceContext";
import { persistenceErrorMessage } from "../../../../state/directoryContext";
import { LabelChip } from "./LabelChip";
import { LabelColorPicker } from "./LabelColorPicker";
import { NewLabelForm } from "./NewLabelForm";

const customersText = (count: number) => (count === 0 ? "Nadie la tiene" : `${count} ${count === 1 ? "cliente" : "clientes"}`);

/**
 * El catálogo de etiquetas del negocio: crear, cambiar el color, cambiar el nombre y borrar, viendo cuántos clientes lleva cada una.
 * Crear y cambiar el color lo hace todo el que atiende; el nombre y borrar, solo quien configura el negocio (`canManage`), porque
 * afecta a todos sus clientes. Cada cambio avisa con `onChanged` para que Clientes se vuelva a cargar.
 */
export function LabelsDialog({ labels, canManage, onChanged, onClose }: { labels: Label[]; canManage: boolean; onChanged: () => void; onClose: () => void }) {
  const commerce = useCommerce();
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<{ id: string; name: string; problem: string | null } | null>(null);
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
  const recolor = async (label: Label, color: LabelColor) => setProblem(color === label.color ? null : await run(() => commerce.updateLabel(label.id, { color })));
  const rename = async (label: Label) => {
    if (!editing) return;
    const found = nameProblem(editing.name, labels, label.id) ?? (editing.name.trim() === label.name ? null : await run(() => commerce.updateLabel(label.id, { name: editing.name.trim() })));
    setEditing(found ? { ...editing, problem: found } : null);
  };
  const remove = async (label: Label) => {
    setProblem(await run(() => commerce.deleteLabel(label.id)));
    setDeleting(null);
  };

  return (
    <Dialog title="Etiquetas" description="Organiza a tus clientes a tu manera. Se las pones a cada uno desde su ficha." onClose={onClose}>
      <div className="labels-dialog">
        <NewLabelForm existing={labels} saving={saving} onCreate={(name, color) => run(() => commerce.createLabel(name, color))} />
        {problem && (
          <p className="field__message field__message--error" role="alert">
            {problem}
          </p>
        )}
        {labels.length === 0 ? (
          <p className="card-section__empty">Todavía no tienes etiquetas. Crea la primera arriba.</p>
        ) : (
          <ul className="labels-list" aria-label="Tus etiquetas">
            {labels.map((label) => (
              <li key={label.id} className="labels-list__item" aria-label={label.name}>
                {editing?.id === label.id ? (
                  <form
                    className="labels-list__rename"
                    aria-label={`Cambiar el nombre de ${label.name}`}
                    noValidate
                    onSubmit={(event) => {
                      event.preventDefault();
                      void rename(label);
                    }}
                  >
                    <TextField label="Nombre" value={editing.name} onChange={(name) => setEditing({ ...editing, name })} maxLength={MAX_LABEL_NAME} error={editing.problem ?? undefined} />
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
                    <span className="labels-list__main">
                      <LabelChip label={label} />
                      <span className="labels-list__count">{customersText(label.customers)}</span>
                    </span>
                    <LabelColorPicker value={label.color} label={`Color de ${label.name}`} disabled={saving} onChange={(color) => void recolor(label, color)} />
                    {canManage && (
                      <span className="labels-list__actions">
                        {deleting === label.id ? (
                          <>
                            <span className="labels-list__count">{label.customers > 0 ? "Sus clientes solo la pierden." : "¿Borrarla?"}</span>
                            <button type="button" className="link-button link-button--danger" disabled={saving} onClick={() => void remove(label)}>
                              Sí, borrar
                            </button>
                            <button type="button" className="link-button" onClick={() => setDeleting(null)}>
                              No
                            </button>
                          </>
                        ) : (
                          <>
                            <button type="button" className="link-button" aria-label={`Cambiar el nombre de ${label.name}`} onClick={() => setEditing({ id: label.id, name: label.name, problem: null })}>
                              Renombrar
                            </button>
                            <button type="button" className="link-button" aria-label={`Borrar la etiqueta ${label.name}`} onClick={() => setDeleting(label.id)}>
                              Borrar
                            </button>
                          </>
                        )}
                      </span>
                    )}
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
        {!canManage && labels.length > 0 && <p className="card-section__empty">Cambiarles el nombre o borrarlas es del dueño o de un administrador.</p>}
      </div>
    </Dialog>
  );
}
