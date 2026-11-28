import { useState } from "react";
import type { Assignee } from "../../../../domain/commerce/customerCard";
import type { NewReminderInput, Reminder } from "../../../../domain/commerce/reminders";
import type { CardResult } from "../../../../state/useCustomerCard";
import { ReminderComposer } from "../reminders/ReminderComposer";
import { ReminderItem } from "../reminders/ReminderItem";

/** Qué hay que hacer con este cliente y cuándo: los pendientes por fecha, el formulario para uno nuevo y, aparte, los ya hechos. */
export function RemindersSection({
  reminders,
  assignees,
  viewerId,
  saving,
  onAdd,
  onMark,
  onDelete,
}: {
  reminders: Reminder[];
  assignees: Assignee[];
  viewerId: string | null;
  saving: boolean;
  onAdd: (input: NewReminderInput) => Promise<CardResult>;
  onMark: (reminderId: string, done: boolean) => Promise<CardResult>;
  onDelete: (reminderId: string) => Promise<CardResult>;
}) {
  const [problem, setProblem] = useState<string | null>(null);
  const [showDone, setShowDone] = useState(false);
  const pending = reminders.filter((item) => !item.doneAt);
  const done = reminders.filter((item) => item.doneAt);
  const report = (result: CardResult) => setProblem(result.ok ? null : result.message);

  return (
    <section className="card-section" aria-label="Recordatorios">
      <header className="card-section__head">
        <h3>Recordatorios</h3>
        <span className="card-section__aside">{pending.length === 0 ? "nada pendiente" : `${pending.length} pendiente${pending.length === 1 ? "" : "s"}`}</span>
      </header>
      {pending.length > 0 && (
        <ul className="reminder-list">
          {pending.map((item) => (
            <ReminderItem key={item.id} reminder={item} busy={saving} onToggle={() => void onMark(item.id, true).then(report)} onDelete={() => void onDelete(item.id).then(report)} />
          ))}
        </ul>
      )}
      {problem && (
        <p className="field__message field__message--error" role="alert">
          {problem}
        </p>
      )}
      <ReminderComposer
        assignees={assignees}
        viewerId={viewerId}
        saving={saving}
        onCreate={async (input) => {
          const result = await onAdd(input);
          return result.ok ? null : result.message;
        }}
      />
      {done.length > 0 && (
        <>
          <button type="button" className="link-button" aria-expanded={showDone} onClick={() => setShowDone(!showDone)}>
            {showDone ? "Ocultar los hechos" : `Ver los hechos (${done.length})`}
          </button>
          {showDone && (
            <ul className="reminder-list">
              {done.map((item) => (
                <ReminderItem key={item.id} reminder={item} busy={saving} onToggle={() => void onMark(item.id, false).then(report)} onDelete={() => void onDelete(item.id).then(report)} />
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
