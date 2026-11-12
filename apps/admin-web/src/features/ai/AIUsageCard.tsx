import { Icon, type IconName } from "../../components/ui/Icon";
import { Card } from "../../components/ui/Layout";
import { formatCost, formatCount, formatTokens } from "../../domain/assistant/usage";
import { useAIUsage } from "../../state/useAIUsage";

/** Cuánto gastó la IA de este negocio en 30 días: respuestas, tokens y el costo que informó OpenRouter. */
export function AIUsageCard() {
  const state = useAIUsage();
  const usage = state.status === "ready" ? state.usage : null;
  const cost = usage ? formatCost(usage.costUsd) : null;
  const metrics: { label: string; value: string; icon: IconName }[] = [
    { label: "Respuestas de la IA", value: usage ? formatCount(usage.replies) : "—", icon: "chat" },
    { label: "Tokens usados", value: usage ? formatTokens(usage.promptTokens + usage.completionTokens) : "—", icon: "bolt" },
    { label: "Costo en OpenRouter", value: cost ?? "—", icon: "wallet" },
  ];

  return (
    <Card
      icon="chart"
      tone="amber"
      title="Consumo de los últimos 30 días"
      description="Cada respuesta de tu asistente, también las de Probar, se cobra en tu cuenta de OpenRouter. El detalle exacto está en openrouter.ai, en Activity."
    >
      {state.status === "error" && <p className="field__hint">No se pudo cargar el consumo: {state.message}</p>}
      <div className="usage__grid" aria-busy={state.status === "loading"}>
        {metrics.map((metric) => (
          <div key={metric.label} className="metric">
            <span className="metric__icon">
              <Icon name={metric.icon} size={18} />
            </span>
            <span className="metric__value">{metric.value}</span>
            <span className="metric__label">{metric.label}</span>
          </div>
        ))}
      </div>
      {usage && usage.replies > 0 && cost === null && (
        <p className="field__hint">OpenRouter no informó el costo de estas respuestas; consúltalo en tu cuenta.</p>
      )}
    </Card>
  );
}
