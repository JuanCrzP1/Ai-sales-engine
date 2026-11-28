import { useState, type FormEvent } from "react";
import { Button } from "../../../../components/ui/Button";
import { TextAreaField } from "../../../../components/ui/FormFields";
import { MAX_NOTE, type CustomerNote } from "../../../../domain/commerce/customerCard";
import { relativeTime } from "../../../../domain/inbox/format";
import type { CardResult } from "../../../../state/useCustomerCard";

/** Lo que el equipo anota de este cliente. El cliente nunca lo ve. Cada nota queda a nombre de quien la escribió. */
export function NotesSection({
  notes,
  saving,
  onAdd,
  onDelete,
}: {
  notes: CustomerNote[];
  saving: boolean;
  onAdd: (body: string) => Promise<CardResult>;
  onDelete: (noteId: string) => Promise<CardResult>;
}) {
  const [body, setBody] = useState("");
  const [problem, setProblem] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!body.trim()) return setProblem("Escribe la nota.");
    const result = await onAdd(body);
    if (result.ok) setBody("");
    setProblem(result.ok ? null : result.message);
  };
  const remove = async (noteId: string) => {
    const result = await onDelete(noteId);
    setDeleting(null);
    setProblem(result.ok ? null : result.message);
  };

  return (
    <section className="card-section" aria-label="Notas">
      <header className="card-section__head">
        <h3>Notas</h3>
        <span className="card-section__aside">solo las ve tu equipo</span>
      </header>
      <form className="note-form" aria-label="Agregar una nota" noValidate onSubmit={submit}>
        <TextAreaField label="Nota nueva" rows={2} value={body} onChange={setBody} maxLength={MAX_NOTE} placeholder="Ej.: prefiere que lo llamen en la tarde" error={problem ?? undefined} />
        <Button type="submit" size="small" variant="secondary" disabled={saving}>
          Agregar nota
        </Button>
      </form>
      {notes.length > 0 && (
        <ul className="note-list">
          {notes.map((note) => (
            <li key={note.id} className="note">
              <p className="note__body">{note.body}</p>
              <span className="note__meta">
                <span>
                  {note.author ?? "Tu equipo"} · <time dateTime={note.createdAt}>{relativeTime(note.createdAt)}</time>
                </span>
                {deleting === note.id ? (
                  <>
                    <button type="button" className="link-button link-button--danger" disabled={saving} onClick={() => void remove(note.id)}>
                      Sí, borrar
                    </button>
                    <button type="button" className="link-button" onClick={() => setDeleting(null)}>
                      No
                    </button>
                  </>
                ) : (
                  <button type="button" className="link-button" aria-label={`Borrar la nota «${note.body.slice(0, 40)}»`} onClick={() => setDeleting(note.id)}>
                    Borrar
                  </button>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
