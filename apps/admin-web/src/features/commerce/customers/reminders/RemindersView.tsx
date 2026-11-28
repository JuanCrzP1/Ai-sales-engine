import { useState } from "react";
import { Button } from "../../../../components/ui/Button";
import { Alert } from "../../../../components/ui/Feedback";
import { byBucket, type Reminder, type ReminderBucket } from "../../../../domain/commerce/reminders";
import { useCommerce } from "../../../../state/commerceContext";
import { persistenceErrorMessage } from "../../../../state/directoryContext";
import type { Loadable } from "../../../../state/useConversations";
import { useReminders } from "../../../../state/useReminders";
import { ReminderItem } from "./ReminderItem";

type Tab = ReminderBucket | "done";
const TABS: { tab: Tab; label: string }[] = [
  { tab: "overdue", label: "Vencidos" },
  { tab: "today", label: "Hoy" },
  { tab: "upcoming", label: "Próximos" },
  { tab: "done", label: "Hechos" },
];
const EMPTY: Record<Tab, string> = {
  overdue: "Nada vencido. ¡Vas al día!",
  today: "Nada para hoy. Agrega recordatorios desde la ficha de cada cliente.",
  upcoming: "Nada programado para los próximos días.",
  done: "Aún no hay recordatorios hechos.",
};

/**
 * Los recordatorios del equipo en un solo lugar: vencidos, de hoy, próximos y hechos, los míos o los de todo el equipo (`mine`, solo
 * con cuentas). Marcar uno lo saca de la lista; el nombre del cliente abre su ficha. `open` son los pendientes, que la página ya
 * cargó (también cuenta los vencidos para su insignia).
 */
export function RemindersView({
  open,
  version,
  mine,
  canChooseMine,
  onMine,
  onOpenCustomer,
  onChanged,
}: {
  open: Loadable<Reminder[]>;
  version: number;
  mine: boolean;
  canChooseMine: boolean;
  onMine: (mine: boolean) => void;
  onOpenCustomer: (conversationId: string) => void;
  onChanged: () => void;
}) {
  const commerce = useCommerce();
  const [tab, setTab] = useState<Tab>("today");
  const done = useReminders(version, { done: true, mine, enabled: tab === "done" });
  const [busyId, setBusyId] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const groups = byBucket(open.status === "ready" ? open.data : []);
  const shown = tab === "done" ? done : open;
  const items = tab === "done" ? (done.status === "ready" ? done.data : []) : groups[tab];

  const toggle = async (reminder: Reminder) => {
    setBusyId(reminder.id);
    try {
      await commerce.setReminderDone(reminder.id, reminder.doneAt === null);
      setProblem(null);
      onChanged();
    } catch (error) {
      setProblem(persistenceErrorMessage(error));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="reminders-view">
      <div className="reminders-view__bar">
        <div className="segmented-tabs" role="group" aria-label="Cuándo">
          {TABS.map((item) => {
            const count = item.tab === "done" ? null : groups[item.tab].length;
            return (
              <button
                key={item.tab}
                type="button"
                className={`segmented-tabs__option${item.tab === "overdue" && count ? " segmented-tabs__option--alert" : ""}`}
                aria-pressed={tab === item.tab}
                onClick={() => setTab(item.tab)}
              >
                {item.label}
                {count !== null && open.status === "ready" && <span className="segmented-tabs__count">{count}</span>}
              </button>
            );
          })}
        </div>
        {canChooseMine && (
          <div className="segmented-tabs" role="group" aria-label="De quién">
            <button type="button" className="segmented-tabs__option" aria-pressed={mine} onClick={() => onMine(true)}>
              Míos
            </button>
            <button type="button" className="segmented-tabs__option" aria-pressed={!mine} onClick={() => onMine(false)}>
              De todo el equipo
            </button>
          </div>
        )}
      </div>
      {problem && (
        <p className="field__message field__message--error" role="alert">
          {problem}
        </p>
      )}
      {shown.status === "loading" && <p className="data-panel__status" role="status">Cargando recordatorios…</p>}
      {shown.status === "error" && (
        <div className="data-panel__status">
          <Alert tone="danger" title="No se pudieron cargar los recordatorios">
            <p>{shown.message}</p>
            <Button size="small" variant="secondary" onClick={onChanged}>
              Reintentar
            </Button>
          </Alert>
        </div>
      )}
      {shown.status === "ready" && items.length === 0 && <p className="reminders-view__empty">{EMPTY[tab]}</p>}
      {items.length > 0 && (
        <ul className="reminder-list reminder-list--wide" aria-label={TABS.find((item) => item.tab === tab)!.label}>
          {items.map((reminder) => (
            <ReminderItem
              key={reminder.id}
              reminder={reminder}
              showCustomer
              busy={busyId === reminder.id}
              onToggle={() => void toggle(reminder)}
              onOpenCustomer={() => onOpenCustomer(reminder.conversationId)}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
