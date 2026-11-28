import { Link } from "react-router-dom";
import { boughtText, customerName } from "../../../domain/commerce/pipeline";
import type { BoardStage, Customer } from "../../../domain/commerce/types";
import { relativeTime } from "../../../domain/inbox/format";
import { CHANNEL_LABELS, type Channel } from "../../../domain/inbox/types";
import { ContactAvatar } from "../../../layout/ContactAvatar";
import { MoveMenu } from "./MoveMenu";

/**
 * Un cliente en el tablero: quién es (el canal va en su foto), hace cuánto escribió, si espera a una persona, lo que lleva comprado y,
 * si no compró, por qué. Se arrastra a otra columna o se mueve con «Mover a…». Tocarlo abre su chat.
 */
export function CustomerCard({
  customer,
  chatPath,
  dragging = false,
  busy = false,
  onMove,
  onDragStart,
  onDragEnd,
}: {
  customer: Customer;
  chatPath: string;
  dragging?: boolean;
  busy?: boolean;
  onMove: (stage: BoardStage) => void;
  onDragStart: () => void;
  onDragEnd: () => void;
}) {
  const name = customerName(customer);
  const bought = boughtText(customer);
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
      <Link className="customer-card__open" to={chatPath} draggable={false} aria-label={`Abrir el chat de ${name}`}>
        <ContactAvatar name={name} channel={customer.channel as Channel} size="sm" />
        <span className="customer-card__who">
          <strong className="customer-card__name">{name}</strong>
          <time className="customer-card__meta" dateTime={customer.lastMessageAt} title="Su último mensaje">
            {relativeTime(customer.lastMessageAt)}
          </time>
        </span>
      </Link>
      {customer.needsHuman && <span className="handoff-badge">Espera a una persona</span>}
      {bought && <span className="customer-card__bought">{bought}</span>}
      {customer.stage === "lost" && <span className="customer-card__reason">{customer.lostReason ? `«${customer.lostReason}»` : "Sin motivo anotado"}</span>}
      <span className="customer-card__footer">
        <span className="customer-card__channel" title={CHANNEL_LABELS[customer.channel as Channel] ?? customer.channel}>
          {customer.messageCount} {customer.messageCount === 1 ? "mensaje" : "mensajes"}
        </span>
        <MoveMenu current={customer.stage} label={`Mover a ${name} a otra etapa`} disabled={busy} onMove={onMove} />
      </span>
    </article>
  );
}
