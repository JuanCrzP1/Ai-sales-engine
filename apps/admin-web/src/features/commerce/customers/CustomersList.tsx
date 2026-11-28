import { useMemo } from "react";
import { Button, LinkButton } from "../../../components/ui/Button";
import { Alert } from "../../../components/ui/Feedback";
import { Icon } from "../../../components/ui/Icon";
import { customerName } from "../../../domain/commerce/pipeline";
import { BOARD_STAGES, STAGE_HINTS, STAGE_LABELS, formatMoney, type BoardStage, type Customer } from "../../../domain/commerce/types";
import { relativeTime } from "../../../domain/inbox/format";
import { CHANNEL_LABELS, type Channel } from "../../../domain/inbox/types";
import { ContactAvatar } from "../../../layout/ContactAvatar";
import { useCommerceData } from "../../../state/useCommerceData";
import { MoveMenu } from "./MoveMenu";

/**
 * La lista de clientes: todos en una tabla, con las etapas arriba para filtrar. `version` cambia cuando algo se movió, se vendió o se
 * eliminó, y la lista se vuelve a pedir.
 */
export function CustomersList({
  version,
  query,
  stage,
  busyId,
  chatPath,
  onStage,
  onMove,
  onSell,
  onDelete,
}: {
  version: number;
  query: string;
  stage: BoardStage | null;
  busyId: string | null;
  chatPath: (customer: Customer) => string;
  onStage: (stage: BoardStage | null) => void;
  onMove: (customer: Customer, stage: BoardStage) => void;
  onSell: (customer: Customer) => void;
  onDelete: (customer: Customer) => void;
}) {
  const { state, reload } = useCommerceData((commerce) => commerce.customers(), [version]);
  const all = state.status === "ready" ? state.data : [];
  const counts = useMemo(() => Object.fromEntries(BOARD_STAGES.map((item) => [item, all.filter((customer) => customer.stage === item).length])) as Record<BoardStage, number>, [all]);
  const text = query.trim().toLowerCase();
  const shown = all.filter((customer) => (!stage || customer.stage === stage) && (!text || `${customer.name ?? ""} ${customer.contact}`.toLowerCase().includes(text)));

  return (
    <>
      <div className="pipeline pipeline--inline" role="group" aria-label="Etapas">
        {BOARD_STAGES.map((item) => (
          <button key={item} type="button" className={`pipeline__stage stage-tone--${item}`} aria-pressed={stage === item} onClick={() => onStage(stage === item ? null : item)} title={STAGE_HINTS[item]}>
            <span className="pipeline__count">{state.status === "ready" ? counts[item] : "—"}</span>
            <span className="pipeline__label">{STAGE_LABELS[item]}</span>
          </button>
        ))}
      </div>

      <p className="data-panel__count data-panel__count--line">
        {state.status === "ready" ? `${shown.length} ${shown.length === 1 ? "cliente" : "clientes"}` : ""}
        {stage && (
          <button type="button" className="link-button" onClick={() => onStage(null)}>
            Quitar filtro
          </button>
        )}
      </p>

      {state.status === "loading" && <p className="data-panel__status" role="status">Cargando clientes…</p>}
      {state.status === "error" && (
        <div className="data-panel__status">
          <Alert tone="danger" title="No se pudieron cargar los clientes">
            <p>{state.message}</p>
            <Button size="small" variant="secondary" onClick={reload}>
              Reintentar
            </Button>
          </Alert>
        </div>
      )}
      {state.status === "ready" && shown.length === 0 && <p className="data-panel__status">Nadie coincide con ese filtro.</p>}
      {shown.length > 0 && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Cliente</th>
                <th scope="col">Etapa</th>
                <th scope="col">Canal</th>
                <th scope="col">Último mensaje</th>
                <th scope="col" className="numeric">Compras</th>
                <th scope="col">
                  <span className="visually-hidden">Acciones</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {shown.map((customer) => {
                const name = customerName(customer);
                return (
                  <tr key={customer.conversationId} aria-busy={busyId === customer.conversationId || undefined}>
                    <td>
                      <span className="person">
                        <ContactAvatar name={name} channel={customer.channel as Channel} size="sm" />
                        <span className="person__text">
                          <strong>{name}</strong>
                          <span>+{customer.contact}</span>
                        </span>
                      </span>
                    </td>
                    <td>
                      <span className={`stage-pill stage-tone--${customer.stage}`}>{STAGE_LABELS[customer.stage]}</span>
                      {customer.needsHuman && <span className="handoff-badge">Espera a una persona</span>}
                      {customer.stage === "lost" && customer.lostReason && <span className="cell-sub">«{customer.lostReason}»</span>}
                    </td>
                    <td>{CHANNEL_LABELS[customer.channel as Channel] ?? customer.channel}</td>
                    <td>
                      <time dateTime={customer.lastMessageAt}>{relativeTime(customer.lastMessageAt)}</time>
                      <span className="cell-sub">{customer.messageCount} mensajes</span>
                    </td>
                    <td className="numeric">
                      {Object.keys(customer.spent).length === 0
                        ? "—"
                        : Object.entries(customer.spent).map(([currency, amount]) => <span key={currency} className="money">{formatMoney(amount, currency)}</span>)}
                    </td>
                    <td className="row-actions">
                      <LinkButton variant="ghost" size="small" to={chatPath(customer)}>
                        Ver chat
                      </LinkButton>
                      <Button size="small" variant="secondary" onClick={() => onSell(customer)}>
                        Registrar venta
                      </Button>
                      <MoveMenu current={customer.stage} label={`Mover a ${name} a otra etapa`} disabled={busyId === customer.conversationId} onMove={(target) => onMove(customer, target)} />
                      <button type="button" className="row-delete" aria-label={`Eliminar a ${name}`} title="Eliminar" onClick={() => onDelete(customer)}>
                        <Icon name="trash" size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
