import { dueText, type Reminder } from "../../../../domain/commerce/reminders";
import { relativeTime } from "../../../../domain/inbox/format";

/**
 * Un recordatorio: el círculo para marcarlo hecho, qué es, de quién (y de qué cliente, en la vista de todos) y cuándo toca. Hecho, se
 * ve tachado con quién lo hizo. `onOpenCustomer` (opcional) convierte el nombre del cliente en un botón que abre su ficha.
 */
export function ReminderItem({
  reminder,
  busy = false,
  showCustomer = false,
  onToggle,
  onOpenCustomer,
  onDelete,
}: {
  reminder: Reminder;
  busy?: boolean;
  showCustomer?: boolean;
  onToggle: () => void;
  onOpenCustomer?: () => void;
  onDelete?: () => void;
}) {
  const done = reminder.doneAt !== null;
  const due = dueText(reminder.dueAt);
  const customer = reminder.customerName || `+${reminder.customerContact}`;
  return (
    <li className={`reminder${done ? " reminder--done" : ` reminder--${due.tone}`}`}>
      <button
        type="button"
        className="reminder__check"
        aria-pressed={done}
        aria-label={done ? `Volver a abrir «${reminder.title}»` : `Marcar «${reminder.title}» como hecho`}
        disabled={busy}
        onClick={onToggle}
      >
        {done && (
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true">
            <path d="m5 12 5 5 9-10" />
          </svg>
        )}
      </button>
      <span className="reminder__text">
        <span className="reminder__title">{reminder.title}</span>
        <span className="reminder__meta">
          {showCustomer &&
            (onOpenCustomer ? (
              <button type="button" className="link-button reminder__customer" onClick={onOpenCustomer}>
                {customer}
              </button>
            ) : (
              <span>{customer}</span>
            ))}
          {showCustomer && <span aria-hidden="true">·</span>}
          <span>{done ? `Hecho ${relativeTime(reminder.doneAt!)}${reminder.doneBy ? ` por ${reminder.doneBy}` : ""}` : (reminder.assignee?.label ?? "Sin responsable")}</span>
          {onDelete && (
            <button type="button" className="link-button" aria-label={`Borrar «${reminder.title}»`} disabled={busy} onClick={onDelete}>
              Borrar
            </button>
          )}
        </span>
      </span>
      {!done && <span className={`reminder__due reminder__due--${due.tone}`}>{due.text}</span>}
    </li>
  );
}
