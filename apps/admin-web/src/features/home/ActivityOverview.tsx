import { useParams } from "react-router-dom";
import { LinkButton } from "../../components/ui/Button";
import { Icon, type IconName } from "../../components/ui/Icon";
import { CONVERSATIONS_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useBusinessActivity } from "../../state/useConversations";

/** Lo que pasó hoy en el negocio: lo primero que ve el dueño al entrar. */
export function ActivityOverview() {
  const { slug = "" } = useParams();
  const pathTo = useWorkspacePath();
  const activity = useBusinessActivity(slug);
  const data = activity.status === "ready" ? activity.data : null;
  const metrics: { label: string; value: number | null; icon: IconName }[] = [
    { label: "Conversaciones hoy", value: data?.conversationsToday ?? null, icon: "inbox" },
    { label: "Mensajes hoy", value: data?.messagesToday ?? null, icon: "chat" },
    { label: "Esperan a una persona", value: data?.waitingHuman ?? null, icon: "headset" },
    { label: "Conversaciones en total", value: data?.conversations ?? null, icon: "users" },
  ];

  return (
    <section className="activity" aria-labelledby="actividad-titulo">
      <div className="activity__head">
        <h2 id="actividad-titulo" className="section-heading">
          Hoy en tu negocio
        </h2>
        <LinkButton to={pathTo(CONVERSATIONS_ITEM.path)} size="small">
          Ver conversaciones
        </LinkButton>
      </div>
      {activity.status === "error" && <p className="field__hint">No se pudo cargar la actividad: {activity.message}</p>}
      <div className="activity__grid">
        {metrics.map((metric) => (
          <div key={metric.label} className="metric">
            <span className="metric__icon">
              <Icon name={metric.icon} size={18} />
            </span>
            <span className="metric__value">{metric.value ?? "—"}</span>
            <span className="metric__label">{metric.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
