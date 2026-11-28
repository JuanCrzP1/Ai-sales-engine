import { Icon } from "../../../components/ui/Icon";
import { initialsOf } from "../../../domain/commerce/customerCard";
import { shownLabels } from "../../../domain/commerce/labels";
import { boughtText, customerName } from "../../../domain/commerce/pipeline";
import { dueShort, dueText } from "../../../domain/commerce/reminders";
import { formatMoney, type BoardStage, type Customer } from "../../../domain/commerce/types";
import { relativeTime } from "../../../domain/inbox/format";
import { CHANNEL_LABELS, type Channel } from "../../../domain/inbox/types";
import { ContactAvatar } from "../../../layout/ContactAvatar";
import { LabelChip } from "./labels/LabelChip";
import { MoveMenu } from "./MoveMenu";

/**
 * Un cliente en el tablero: quién es (el canal va en su foto), hace cuánto escribió, cuánto vale, si espera a una persona, lo que
 * lleva comprado, por qué no compró y quién lo atiende. Se arrastra a otra columna o se mueve con «Mover a…». Tocarlo abre su ficha.
 */
export function CustomerCard({
  customer,
  dragging = false,
  busy = false,
  onOpen,
  onMove,
  onDragStart,
  onDragEnd,
}: {
  customer: Customer;
  dragging?: boolean;
  busy?: boolean;
  onOpen: () => void;
  onMove: (stage: BoardStage) => void;
  onDragStart: () => void;
  onDragEnd: () => void;
}) {
  const name = customerName(customer);
  const bought = boughtText(customer);
  const labels = shownLabels(customer.labels);
  const next = customer.nextReminder ? dueShort(customer.nextReminder.dueAt) : null;
  const nextFull = customer.nextReminder ? `${dueText(customer.nextReminder.dueAt).text}: ${customer.nextReminder.title}` : "";
  return (
    <article
      className={`customer-card${dragging ? " customer-card--dragging" : ""}${busy ? " customer-card--busy" : ""}`}
      aria-label={name}
      aria-busy={busy || undefined}
      draggable={!busy}
      onDragStart={(event) => {
        event.dataTransfer.setData("text/plain", customer.conversationId);
        event.dataTransfer.effectAllowed = "move";
        onDragStart();
      }}
      onDragEnd={onDragEnd}
    >
      <button type="button" className="customer-card__open" onClick={onOpen} aria-label={`Abrir la ficha de ${name}`}>
        <ContactAvatar name={name} channel={customer.channel as Channel} size="sm" />
        <span className="customer-card__who">
          <strong className="customer-card__name">{name}</strong>
          <time className="customer-card__meta" dateTime={customer.lastMessageAt} title="Su último mensaje">
            {relativeTime(customer.lastMessageAt)}
          </time>
        </span>
      </button>
      {customer.deal && <span className="customer-card__value">{formatMoney(customer.deal.amount, customer.deal.currency)}</span>}
      {customer.labels.length > 0 && (
        <span className="label-row" aria-label={`Etiquetas: ${customer.labels.map((label) => label.name).join(", ")}`}>
          {labels.shown.map((label) => (
            <LabelChip key={label.id} label={label} />
          ))}
          {labels.more > 0 && <span className="label-chip label-chip--more">+{labels.more}</span>}
        </span>
      )}
      {customer.needsHuman && <span className="handoff-badge">Espera a una persona</span>}
      {customer.nextReminder && next && (
        <span className={`next-reminder next-reminder--${next.tone}`} title={nextFull} aria-label={`Recordatorio. ${nextFull}`}>
          <Icon name="clock" size={13} />
          <span className="next-reminder__text">{next.text}</span>
        </span>
      )}
      {bought && <span className="customer-card__bought">{bought}</span>}
      {customer.stage === "lost" && <span className="customer-card__reason">{customer.lostReason ? `«${customer.lostReason}»` : "Sin motivo anotado"}</span>}
      <span className="customer-card__footer">
        <span className="customer-card__channel" title={CHANNEL_LABELS[customer.channel as Channel] ?? customer.channel}>
          {customer.messageCount} {customer.messageCount === 1 ? "mensaje" : "mensajes"}
        </span>
        <span className="customer-card__tools">
          {customer.owner && (
            <span className="owner-chip" title={`Lo atiende ${customer.owner.label}`} aria-label={`Lo atiende ${customer.owner.label}`}>
              {initialsOf(customer.owner.label)}
            </span>
          )}
          <MoveMenu current={customer.stage} label={`Mover a ${name} a otra etapa`} disabled={busy} onMove={onMove} />
        </span>
      </span>
    </article>
  );
}
