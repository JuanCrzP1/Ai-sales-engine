import { Button } from "../../../../components/ui/Button";
import { formatMoney, type Sale } from "../../../../domain/commerce/types";
import { relativeTime } from "../../../../domain/inbox/format";

/** Lo que ha comprado: cada venta con su valor y cuándo fue (las anuladas, marcadas), y el botón para registrar otra. */
export function PurchasesSection({ purchases, onSell }: { purchases: Sale[]; onSell: () => void }) {
  return (
    <section className="card-section" aria-label="Compras">
      <header className="card-section__head">
        <h3>Compras</h3>
        <Button size="small" variant="secondary" onClick={onSell}>
          Registrar venta
        </Button>
      </header>
      {purchases.length === 0 ? (
        <p className="card-section__empty">Todavía no ha comprado.</p>
      ) : (
        <ul className="purchase-list">
          {purchases.map((sale) => (
            <li key={sale.id} className={`purchase${sale.status === "cancelled" ? " purchase--cancelled" : ""}`}>
              <span className="purchase__what">
                <strong>{sale.description}</strong>
                <span>
                  <time dateTime={sale.createdAt}>{relativeTime(sale.createdAt)}</time>
                  {sale.status === "cancelled" && " · Anulada"}
                </span>
              </span>
              <span className="purchase__money">{formatMoney(sale.amount, sale.currency)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
