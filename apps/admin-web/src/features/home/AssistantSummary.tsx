import { Badge } from "../../components/ui/Feedback";
import { Icon, type IconName } from "../../components/ui/Icon";
import { labelFor, RESPONSE_LENGTHS, SALES_MODES } from "../../domain/config/options";
import { initials } from "../../lib/text";
import { useConfig } from "../../state/useConfig";

/** Tarjeta de resumen del asistente en el inicio. */
export function AssistantSummary() {
  const { config } = useConfig();
  const { business, offerings, payments, behavior } = config;
  const available = offerings.filter((offering) => offering.available).length;
  const paymentOptions =
    (payments.paymentLinkEnabled && payments.paymentLink.trim() ? 1 : 0) +
    (payments.transferEnabled ? payments.transferMethods.length : 0);
  const name = business.name.trim() || "Tu negocio";

  return (
    <section className="card card--profile">
      <div className="profile">
        <span className="profile__avatar" aria-hidden="true">
          {initials(name)}
        </span>
        <div className="profile__text">
          <h2 className="card__title">{name}</h2>
          <p className="card__description">
            {business.businessType.trim() || "Aún no has indicado a qué se dedica tu negocio."}
          </p>
        </div>
        <Badge tone="neutral">
          <span className="live-dot" aria-hidden="true" />
          Sin conectar
        </Badge>
      </div>
      <div className="stat-grid">
        <Stat icon="box" tone="blue" value={String(available)} label={available === 1 ? "producto o servicio disponible" : "productos o servicios disponibles"} />
        <Stat icon="wallet" tone="green" value={String(paymentOptions)} label={paymentOptions === 1 ? "medio de pago" : "medios de pago"} />
        <Stat icon="tag" tone="violet" value={labelFor(SALES_MODES, business.salesMode)} label="forma de venta" />
        <Stat icon="smile" tone="amber" value={labelFor(RESPONSE_LENGTHS, behavior.responseLength)} label="largo de respuestas" />
      </div>
    </section>
  );
}

interface StatProps {
  icon: IconName;
  tone: "blue" | "green" | "violet" | "amber";
  value: string;
  label: string;
}

function Stat({ icon, tone, value, label }: StatProps) {
  return (
    <div className="stat">
      <span className={`stat__icon stat__icon--${tone}`}>
        <Icon name={icon} size={18} />
      </span>
      <div className="stat__text">
        <p className="stat__value">{value}</p>
        <p className="stat__label">{label}</p>
      </div>
    </div>
  );
}
