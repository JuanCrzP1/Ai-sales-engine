import { Badge } from "../../components/ui/Feedback";
import { Icon, type IconName } from "../../components/ui/Icon";
import { isAvailable, offerEntries, paymentOptionsCount } from "../../domain/config/document";
import { labelFor, OFFER_MODELS, RESPONSE_LENGTHS } from "../../domain/config/options";
import { initials } from "../../lib/text";
import { useConfig } from "../../state/useConfig";
import { useWhatsAppStatus } from "../../state/useWhatsAppStatus";

/** Tarjeta de resumen del asistente en el inicio. */
export function AssistantSummary() {
  const { document } = useConfig();
  const { identity, response_style: style } = document;
  const available = offerEntries(document).filter(isAvailable).length;
  const paymentOptions = paymentOptionsCount(document);
  const name = identity.name.trim() || "Tu negocio";

  return (
    <section className="card card--profile">
      <div className="profile">
        <span className="profile__avatar" aria-hidden="true">
          {initials(name)}
        </span>
        <div className="profile__text">
          <h2 className="card__title">{name}</h2>
          <p className="card__description">{identity.industry.trim() || "Aún no has indicado a qué se dedica tu negocio."}</p>
        </div>
        <WhatsAppBadge />
      </div>
      <div className="stat-grid">
        <Stat icon="box" tone="blue" value={String(available)} label={available === 1 ? "producto o servicio disponible" : "productos o servicios disponibles"} />
        <Stat icon="wallet" tone="green" value={String(paymentOptions)} label={paymentOptions === 1 ? "medio de pago" : "medios de pago"} />
        <Stat icon="tag" tone="violet" value={labelFor(OFFER_MODELS, document.offer.model)} label="forma de venta" />
        <Stat icon="smile" tone="amber" value={labelFor(RESPONSE_LENGTHS, style.length ?? "short")} label="largo de respuestas" />
      </div>
    </section>
  );
}

/** El estado real de WhatsApp: conectado, conectándose o sin conectar (nada mientras se averigua). */
function WhatsAppBadge() {
  const status = useWhatsAppStatus();
  if (status === null) return null;
  const [tone, label] =
    status === "connected" ? (["success", "WhatsApp conectado"] as const) : status === "connecting" ? (["warning", "WhatsApp conectándose"] as const) : (["neutral", "WhatsApp sin conectar"] as const);
  return (
    <Badge tone={tone}>
      <span className={`live-dot${status === "connected" ? " live-dot--on" : ""}`} aria-hidden="true" />
      {label}
    </Badge>
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
