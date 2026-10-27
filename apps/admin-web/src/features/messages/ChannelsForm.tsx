import { CheckboxGroup } from "../../components/ui/ChoiceGroup";
import { Alert, Badge } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Layout";
import { SERVICE_CHANNELS } from "../../domain/config/options";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function ChannelsForm() {
  const [messages, update] = useSection("messages");
  const channelsIssue = useFieldIssue("messages.serviceChannels");

  return (
    <Card title="Canales de atención" description="Por dónde atiende tu negocio. El asistente los menciona cuando el cliente pregunta.">
      <Alert tone="info">
        <p>
          Marcar un canal aquí <strong>no lo conecta</strong>. La conexión de WhatsApp o Telegram se hará en una fase
          posterior; por ahora todos aparecen como sin conectar.
        </p>
      </Alert>
      <CheckboxGroup
        legend="Canales que atiendes"
        name="service-channels"
        options={SERVICE_CHANNELS.map((channel) => ({
          ...channel,
          hint: channel.connector ? "El motor tiene conector para este canal." : "Solo como canal informativo.",
          badge: <Badge tone="neutral">Sin conectar</Badge>,
        }))}
        values={messages.serviceChannels}
        onChange={(serviceChannels) => update({ serviceChannels })}
        issue={channelsIssue}
      />
    </Card>
  );
}
