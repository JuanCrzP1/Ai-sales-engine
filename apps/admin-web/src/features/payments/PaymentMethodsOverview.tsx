import { Badge } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Layout";
import { summarizePaymentMethods, type PaymentMethodSummary } from "../../domain/config/paymentMethods";
import { useConfig } from "../../state/useConfig";

function DataState({ method }: { method: PaymentMethodSummary }) {
  switch (method.dataState) {
    case "configured":
      return method.masked ? <code className="secret-mask">{method.masked}</code> : <Badge tone="success">Guardado</Badge>;
    case "pending":
      return <Badge tone="warning">Sin guardar</Badge>;
    case "unreadable":
      return <Badge tone="danger">No se puede leer</Badge>;
    case "missing":
      return <Badge tone="danger">Falta el dato</Badge>;
  }
}

/** Los métodos de pago de un vistazo: cuáles hay, cuáles se ofrecen y cómo reconocerlos sin ver el dato completo. */
export function PaymentMethodsOverview() {
  const { document, paymentFields, paymentValues } = useConfig();
  const methods = summarizePaymentMethods(document, paymentFields, paymentValues);
  if (methods.length === 0) return null;

  return (
    <Card icon="card" tone="emerald" wide title="Métodos configurados" description="Solo se muestra una parte de cada dato, para reconocerlo.">
      <ul className="item-list" aria-label="Métodos de pago configurados">
        {methods.map((method) => (
          <li key={method.path} className="item-row">
            <div className="item-row__main">
              <span className="item-row__title">
                {method.name}
                <Badge tone={method.active ? "success" : "neutral"}>{method.active ? "Activo" : "Inactivo"}</Badge>
              </span>
              {method.details.length > 0 && <span className="item-row__meta">{method.details.join(" · ")}</span>}
            </div>
            <span className="item-row__price">
              <DataState method={method} />
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
