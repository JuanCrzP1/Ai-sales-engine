import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import { Button, LinkButton } from "../../../../components/ui/Button";
import { Alert } from "../../../../components/ui/Feedback";
import { Icon } from "../../../../components/ui/Icon";
import type { Label } from "../../../../domain/commerce/labels";
import { customerName } from "../../../../domain/commerce/pipeline";
import type { BoardStage, Customer } from "../../../../domain/commerce/types";
import { CHANNEL_LABELS, type Channel } from "../../../../domain/inbox/types";
import { ContactAvatar } from "../../../../layout/ContactAvatar";
import { DealSection } from "./DealSection";
import { FieldsSection } from "./FieldsSection";
import { HistorySection } from "./HistorySection";
import { LabelsSection } from "./LabelsSection";
import { NotesSection } from "./NotesSection";
import { PurchasesSection } from "./PurchasesSection";
import { RemindersSection } from "./RemindersSection";
import { StageSection } from "./StageSection";
import { useCustomerCard } from "../../../../state/useCustomerCard";

/**
 * La ficha de un cliente: un panel que entra por la derecha, sobre el tablero, con todo lo suyo. De arriba abajo: quién es y su
 * chat, en qué etapa va (y cómo moverlo), cuánto vale y quién lo atiende, sus datos propios (los campos del negocio), qué hay que hacer con él (recordatorios), sus etiquetas,
 * las notas del equipo, sus compras y su historial.
 *
 * `version` cambia cuando el tablero mueve algo (la ficha se vuelve a pedir) y `onChanged` avisa al tablero cuando la ficha cambia
 * el valor o el responsable. `locked`: hay una ventana encima (el motivo de «No compró» o la venta) y Escape es de ella.
 */
export function CustomerDrawer({
  conversationId,
  version,
  locked,
  busy,
  labels,
  chatPath,
  onMove,
  onSell,
  onManageLabels,
  canManageFields,
  onManageFields,
  onChanged,
  onClose,
}: {
  conversationId: string;
  version: number;
  locked: boolean;
  busy: boolean;
  /** El catálogo de etiquetas del negocio. */
  labels: Label[];
  chatPath: (customer: Customer) => string;
  onMove: (customer: Customer, stage: BoardStage) => void;
  onSell: (customer: Customer) => void;
  onManageLabels: () => void;
  /** Quien mira configura el negocio: puede crear y cambiar los campos del cliente. */
  canManageFields: boolean;
  onManageFields: () => void;
  onChanged: () => void;
  onClose: () => void;
}) {
  const titleId = useId();
  const panel = useRef<HTMLElement>(null);
  const card = useCustomerCard(conversationId, version, onChanged);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    panel.current?.focus();
    return () => previous?.focus?.();
  }, []);
  useEffect(() => {
    const escape = (event: KeyboardEvent) => event.key === "Escape" && !locked && onClose();
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, [locked, onClose]);

  const data = card.state.status === "ready" ? card.state.data : null;
  const name = data ? customerName(data.customer) : "Cliente";

  return createPortal(
    <div className="customer-drawer__backdrop" onMouseDown={(event) => event.target === event.currentTarget && !locked && onClose()}>
      <aside ref={panel} className="customer-drawer" role="dialog" aria-modal="true" aria-labelledby={titleId} tabIndex={-1}>
        <header className="customer-drawer__head">
          <div className="customer-drawer__top">
            <span className="customer-drawer__kicker">Cliente</span>
            <button type="button" className="customer-drawer__close" aria-label="Cerrar la ficha" onClick={onClose}>
              <Icon name="close" size={18} />
            </button>
          </div>
          <div className="customer-drawer__who">
            {data && <ContactAvatar name={name} channel={data.customer.channel as Channel} />}
            <div className="customer-drawer__identity">
              <h2 id={titleId}>{name}</h2>
              {data && (
                <span>
                  +{data.customer.contact} · {CHANNEL_LABELS[data.customer.channel as Channel] ?? data.customer.channel} · {data.customer.messageCount}{" "}
                  {data.customer.messageCount === 1 ? "mensaje" : "mensajes"}
                </span>
              )}
            </div>
            {data && (
              <LinkButton size="small" to={chatPath(data.customer)}>
                Abrir chat
              </LinkButton>
            )}
          </div>
        </header>

        <div className="customer-drawer__body">
          {card.state.status === "loading" && <p className="card-section__empty" role="status">Cargando la ficha…</p>}
          {card.state.status === "error" && (
            <Alert tone="danger" title="No se pudo cargar la ficha">
              <p>{card.state.message}</p>
              <Button size="small" variant="secondary" onClick={card.reload}>
                Reintentar
              </Button>
            </Alert>
          )}
          {data && (
            <>
              <StageSection customer={data.customer} stageSince={data.stageSince} busy={busy} onMove={(stage) => onMove(data.customer, stage)} />
              <DealSection card={data} saving={card.saving} onUpdate={card.update} />
              <FieldsSection fields={data.fields} saving={card.saving} canManage={canManageFields} onSave={card.setFieldValues} onManage={onManageFields} />
              <RemindersSection
                reminders={data.reminders}
                assignees={data.assignees}
                viewerId={data.viewerId}
                saving={card.saving}
                onAdd={card.addReminder}
                onMark={card.markReminder}
                onDelete={card.deleteReminder}
              />
              <LabelsSection own={data.customer.labels} catalog={labels} saving={card.saving} onSet={card.setLabels} onCreate={card.createLabel} onManage={onManageLabels} />
              <NotesSection notes={data.notes} saving={card.saving} onAdd={card.addNote} onDelete={card.deleteNote} />
              <PurchasesSection purchases={data.purchases} onSell={() => onSell(data.customer)} />
              <HistorySection events={data.events} />
            </>
          )}
        </div>
      </aside>
    </div>,
    document.body,
  );
}
