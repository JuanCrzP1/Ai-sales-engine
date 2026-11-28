import { useState, type FormEvent } from "react";
import { Button } from "../../../../components/ui/Button";
import { SelectField, TextField } from "../../../../components/ui/FormFields";
import { assigneeLabel, type Assignee } from "../../../../domain/commerce/customerCard";
import { MAX_REMINDER_TITLE, fromLocalInput, localInput, quickDueOptions, type NewReminderInput } from "../../../../domain/commerce/reminders";

const NOBODY = "";

/**
 * Un recordatorio nuevo: qué hay que hacer, cuándo (con atajos como «Mañana 9:00 a. m.» o una fecha y hora) y para quién del equipo.
 * Propone a quien lo crea (`viewerId`); sin equipo, no pregunta. `onCreate` devuelve el mensaje si no se pudo, o null.
 */
export function ReminderComposer({
  assignees,
  viewerId,
  saving,
  onCreate,
}: {
  assignees: Assignee[];
  viewerId: string | null;
  saving: boolean;
  onCreate: (input: NewReminderInput) => Promise<string | null>;
}) {
  const options = quickDueOptions();
  const [title, setTitle] = useState("");
  const [due, setDue] = useState(localInput(options[1]!.at));
  const [owner, setOwner] = useState(viewerId ?? NOBODY);
  const [problem, setProblem] = useState<{ field: "title" | "due"; message: string } | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const dueAt = fromLocalInput(due);
    if (!title.trim()) return setProblem({ field: "title", message: "Escribe qué hay que hacer." });
    if (!dueAt) return setProblem({ field: "due", message: "Elige la fecha y la hora." });
    const input: NewReminderInput = { title: title.trim(), dueAt };
    if (assignees.length > 0) input.assigneeId = owner || null;
    const failed = await onCreate(input);
    setProblem(failed ? { field: "title", message: failed } : null);
    if (!failed) setTitle("");
  };

  return (
    <form className="reminder-composer" aria-label="Agregar un recordatorio" noValidate onSubmit={submit}>
      <TextField
        label="Nuevo recordatorio"
        value={title}
        onChange={setTitle}
        maxLength={MAX_REMINDER_TITLE}
        placeholder="Ej.: llamarlo para cerrar"
        error={problem?.field === "title" ? problem.message : undefined}
      />
      <div className="reminder-composer__when" role="group" aria-label="Cuándo">
        {options.map((option) => (
          <button key={option.label} type="button" className="reminder-composer__chip" aria-pressed={localInput(option.at) === due} onClick={() => setDue(localInput(option.at))}>
            {option.label}
          </button>
        ))}
        <input type="datetime-local" className="input reminder-composer__date" aria-label="Fecha y hora" value={due} onChange={(event) => setDue(event.target.value)} />
      </div>
      {problem?.field === "due" && (
        <p className="field__message field__message--error" role="alert">
          {problem.message}
        </p>
      )}
      <div className="reminder-composer__row">
        {assignees.length > 0 && (
          <SelectField
            label="Para"
            value={owner}
            options={[...assignees.map((member) => ({ value: member.userId, label: member.userId === viewerId ? `Para mí (${member.email ?? "yo"})` : assigneeLabel(member) })), { value: NOBODY, label: "Sin responsable" }]}
            onChange={setOwner}
          />
        )}
        <Button type="submit" size="small" variant="secondary" disabled={saving}>
          Agregar recordatorio
        </Button>
      </div>
    </form>
  );
}
