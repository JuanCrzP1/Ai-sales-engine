import { useMemo, useState } from "react";
import { Button, LinkButton } from "../../components/ui/Button";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import { STAGE_HINTS, STAGE_LABELS, STAGES, formatMoney, type Customer, type Stage } from "../../domain/commerce/types";
import { initials, relativeTime } from "../../domain/inbox/format";
import { CHANNEL_LABELS, type Channel } from "../../domain/inbox/types";
import { CONVERSATIONS_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useCommerceData } from "../../state/useCommerceData";
import { RecordSaleDialog } from "./RecordSaleDialog";

/** Cada persona que le escribió al negocio, en qué etapa va y qué ha comprado. */
export function CustomersPage() {
  const pathTo = useWorkspacePath();
  const { state, reload } = useCommerceData((commerce) => commerce.customers(), []);
  const [stage, setStage] = useState<Stage | null>(null);
  const [query, setQuery] = useState("");
  const [selling, setSelling] = useState<Customer | null>(null);

  const all = state.status === "ready" ? state.data : [];
  const counts = useMemo(() => Object.fromEntries(STAGES.map((item) => [item, all.filter((customer) => customer.stage === item).length])) as Record<Stage, number>, [all]);
  const text = query.trim().toLowerCase();
  const shown = all.filter((customer) => (!stage || customer.stage === stage) && (!text || `${customer.name ?? ""} ${customer.contact}`.toLowerCase().includes(text)));

  return (
    <>
      <PageHeader eyebrow="Atención" title="Clientes" description="Cada persona que le escribió a tu negocio, en qué etapa va y qué ha comprado. La etapa avanza sola con lo que el asistente reconoce en la conversación." />

      <div className="pipeline" role="group" aria-label="Etapas">
        {STAGES.map((item) => (
          <button key={item} type="button" className={`pipeline__stage stage-tone--${item}`} aria-pressed={stage === item} onClick={() => setStage(stage === item ? null : item)} title={STAGE_HINTS[item]}>
            <span className="pipeline__count">{state.status === "ready" ? counts[item] : "—"}</span>
            <span className="pipeline__label">{STAGE_LABELS[item]}</span>
          </button>
        ))}
      </div>

      <section className="data-panel" aria-label="Lista de clientes">
        <div className="data-panel__toolbar">
          <label className="search-field">
            <Icon name="users" size={16} />
            <span className="visually-hidden">Buscar cliente</span>
            <input className="search-field__input" type="search" placeholder="Buscar por nombre o teléfono" value={query} onChange={(event) => setQuery(event.target.value)} />
          </label>
          <span className="data-panel__count">
            {state.status === "ready" ? `${shown.length} ${shown.length === 1 ? "cliente" : "clientes"}` : ""}
            {stage && (
              <button type="button" className="link-button" onClick={() => setStage(null)}>
                Quitar filtro
              </button>
            )}
          </span>
        </div>

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
        {state.status === "ready" && all.length === 0 && (
          <EmptyState title="Aún no hay clientes" description="Cuando alguien le escriba a tu negocio por un canal conectado, aparece aquí con su etapa. Las pruebas del panel no cuentan." />
        )}
        {state.status === "ready" && all.length > 0 && shown.length === 0 && <p className="data-panel__status">Nadie coincide con ese filtro.</p>}
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
                  const name = customer.name || `+${customer.contact}`;
                  return (
                    <tr key={customer.conversationId}>
                      <td>
                        <span className="person">
                          <span className={`person__avatar channel-color--${customer.channel}`} aria-hidden="true">
                            {initials(name)}
                          </span>
                          <span className="person__text">
                            <strong>{name}</strong>
                            <span>+{customer.contact}</span>
                          </span>
                        </span>
                      </td>
                      <td>
                        <span className={`stage-pill stage-tone--${customer.stage}`}>{STAGE_LABELS[customer.stage]}</span>
                        {customer.needsHuman && <span className="handoff-badge">Espera a una persona</span>}
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
                        <LinkButton variant="ghost" size="small" to={`${pathTo(CONVERSATIONS_ITEM.path)}?c=${customer.conversationId}`}>
                          Ver chat
                        </LinkButton>
                        <Button size="small" variant="secondary" onClick={() => setSelling(customer)}>
                          Registrar venta
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selling && (
        <RecordSaleDialog
          customerName={selling.name ?? ""}
          conversationId={selling.conversationId}
          onClose={() => setSelling(null)}
          onSaved={() => {
            setSelling(null);
            reload();
          }}
        />
      )}
    </>
  );
}
