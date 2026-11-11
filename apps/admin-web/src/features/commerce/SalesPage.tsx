import { useState } from "react";
import { Button } from "../../components/ui/Button";
import { KpiTile } from "../../components/ui/Charts";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import { formatMoney, type Customer, type Sale } from "../../domain/commerce/types";
import { fullDate, initials, relativeTime } from "../../domain/inbox/format";
import { persistenceErrorMessage } from "../../state/directoryContext";
import { useCommerceData } from "../../state/useCommerceData";
import { RecordSaleDialog } from "./RecordSaleDialog";

const PERIOD_DAYS = 30;

/** Lo que vende el negocio: las ventas registradas, los pagos que esperan verificación y lo que suman. */
export function SalesPage() {
  const sales = useCommerceData((commerce) => commerce.sales(90), []);
  const pending = useCommerceData((commerce) => commerce.customers({ stage: "payment" }), []);
  const [selling, setSelling] = useState<{ name: string; conversationId: string | null } | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const refresh = () => {
    sales.reload();
    pending.reload();
  };

  const list = sales.state.status === "ready" ? sales.state.data : [];
  const since = Date.now() - PERIOD_DAYS * 86_400_000;
  const recent = list.filter((sale) => sale.status === "confirmed" && Date.parse(sale.createdAt) >= since);
  const revenue = totals(recent);
  const waiting = pending.state.status === "ready" ? pending.state.data : [];

  return (
    <>
      <PageHeader
        eyebrow="Ventas"
        title="Ventas"
        description="Lo que vendes por tus chats. Registra cada venta al verificar el pago: el cliente pasa a «Cliente» y suma en los reportes."
        actions={
          <Button onClick={() => setSelling({ name: "", conversationId: null })}>
            <Icon name="plus" size={16} /> Registrar venta
          </Button>
        }
      />

      <div className="kpi-grid">
        <KpiTile label={`Ventas · ${PERIOD_DAYS} días`} icon="tag" value={sales.state.status === "ready" ? recent.length : "—"} />
        <KpiTile
          label={`Ingresos · ${PERIOD_DAYS} días`}
          icon="wallet"
          value={sales.state.status !== "ready" ? "—" : revenue.length === 0 ? formatMoney(0, "COP") : formatMoney(revenue[0]![1], revenue[0]![0])}
          hint={revenue.length > 1 ? revenue.slice(1).map(([currency, amount]) => formatMoney(amount, currency)).join(" · ") : undefined}
        />
        <KpiTile
          label="Ticket promedio"
          icon="card"
          value={sales.state.status !== "ready" ? "—" : revenue.length === 0 ? "—" : formatMoney(revenue[0]![1] / recent.filter((sale) => sale.currency === revenue[0]![0]).length, revenue[0]![0])}
        />
        <KpiTile label="Pagos por verificar" icon="headset" value={pending.state.status === "ready" ? waiting.length : "—"} hint={waiting.length ? "Revísalos abajo" : undefined} />
      </div>

      {waiting.length > 0 && (
        <section className="data-panel data-panel--attention" aria-labelledby="por-verificar">
          <header className="data-panel__header">
            <h2 id="por-verificar" className="data-panel__title">
              <Icon name="headset" size={18} /> Pagos por verificar
            </h2>
            <p className="data-panel__description">Estos clientes reportaron un pago. Verifícalo en tu cuenta y registra la venta.</p>
          </header>
          <ul className="pending-list">
            {waiting.map((customer) => (
              <PendingPayment key={customer.conversationId} customer={customer} onConfirm={() => setSelling({ name: customer.name ?? "", conversationId: customer.conversationId })} />
            ))}
          </ul>
        </section>
      )}

      <section className="data-panel" aria-labelledby="historial">
        <header className="data-panel__header">
          <h2 id="historial" className="data-panel__title">
            Historial de ventas
          </h2>
          <p className="data-panel__description">Los últimos 90 días. Una venta anulada queda marcada y no suma.</p>
        </header>
        {problem && (
          <div className="data-panel__status">
            <Alert tone="danger">{problem}</Alert>
          </div>
        )}
        {sales.state.status === "loading" && <p className="data-panel__status" role="status">Cargando ventas…</p>}
        {sales.state.status === "error" && (
          <div className="data-panel__status">
            <Alert tone="danger" title="No se pudieron cargar las ventas">
              <p>{sales.state.message}</p>
            </Alert>
          </div>
        )}
        {sales.state.status === "ready" && list.length === 0 && (
          <EmptyState title="Aún no hay ventas" description="Cuando un cliente pague, registra la venta desde aquí, desde Clientes o desde los pagos por verificar." />
        )}
        {list.length > 0 && (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Fecha</th>
                  <th scope="col">Cliente</th>
                  <th scope="col">Qué compró</th>
                  <th scope="col" className="numeric">Valor</th>
                  <th scope="col">Registró</th>
                  <th scope="col">
                    <span className="visually-hidden">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {list.map((sale) => (
                  <SaleRow
                    key={sale.id}
                    sale={sale}
                    onCancel={async () => {
                      setProblem(null);
                      try {
                        await sales.commerce.cancelSale(sale.id);
                        refresh();
                      } catch (error) {
                        setProblem(persistenceErrorMessage(error));
                      }
                    }}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selling && (
        <RecordSaleDialog
          customerName={selling.name}
          conversationId={selling.conversationId}
          onClose={() => setSelling(null)}
          onSaved={() => {
            setSelling(null);
            refresh();
          }}
        />
      )}
    </>
  );
}

function totals(list: Sale[]): [string, number][] {
  const byCurrency = new Map<string, number>();
  for (const sale of list) byCurrency.set(sale.currency, (byCurrency.get(sale.currency) ?? 0) + Number(sale.amount));
  // La moneda en que más se vende va primero.
  return [...byCurrency.entries()].sort((a, b) => b[1] - a[1]);
}

function PendingPayment({ customer, onConfirm }: { customer: Customer; onConfirm: () => void }) {
  const name = customer.name || `+${customer.contact}`;
  return (
    <li className="pending-list__item">
      <span className="person">
        <span className={`person__avatar channel-color--${customer.channel}`} aria-hidden="true">
          {initials(name)}
        </span>
        <span className="person__text">
          <strong>{name}</strong>
          <span>Reportó el pago {relativeTime(customer.lastMessageAt)}</span>
        </span>
      </span>
      <Button size="small" onClick={onConfirm}>
        Confirmar y registrar venta
      </Button>
    </li>
  );
}

function SaleRow({ sale, onCancel }: { sale: Sale; onCancel: () => Promise<void> }) {
  const cancelled = sale.status === "cancelled";
  return (
    <tr className={cancelled ? "data-table__row--muted" : undefined}>
      <td>
        <time dateTime={sale.createdAt}>{fullDate(sale.createdAt)}</time>
      </td>
      <td>{sale.customerName}</td>
      <td>{sale.description}</td>
      <td className="numeric">
        <span className={cancelled ? "money money--cancelled" : "money"}>{formatMoney(sale.amount, sale.currency)}</span>
        {cancelled && <span className="cell-sub">Anulada</span>}
      </td>
      <td className="cell-muted">{sale.createdBy ?? "—"}</td>
      <td className="row-actions">{!cancelled && <ConfirmButton confirmLabel="Sí, anular" onConfirm={onCancel}>Anular</ConfirmButton>}</td>
    </tr>
  );
}
