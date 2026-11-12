import { CheckboxGroup } from "../../components/ui/ChoiceGroup";
import { Alert } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Layout";
import { SERVICE_CHANNELS, withCurrentValues } from "../../domain/config/options";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function ChannelsForm() {
  const [capabilities, update] = useSection("capabilities");
  const channelsIssue = useFieldIssue("capabilities.service_channels");
  const channels = capabilities.service_channels ?? [];

  return (
    <Card icon="plug" tone="indigo" title="Canales de atención" description="Por dónde atiende tu negocio. El asistente los menciona cuando el cliente pregunta.">
      <Alert tone="info">
        <p>
          Marcar un canal aquí <strong>no lo conecta</strong>: solo le dice al asistente por dónde atiendes, para mencionarlo si el cliente
          pregunta. WhatsApp se conecta en <strong>Canales</strong>, y otras plataformas en <strong>Integraciones</strong>.
        </p>
      </Alert>
      <CheckboxGroup
        legend="Canales que atiendes"
        name="service-channels"
        options={withCurrentValues(SERVICE_CHANNELS, channels).map((channel) => ({
          ...channel,
          hint: "connector" in channel && channel.connector ? "El motor tiene conector para este canal." : "Solo como canal informativo.",
        }))}
        values={channels}
        onChange={(service_channels) => update({ service_channels })}
        issue={channelsIssue}
      />
    </Card>
  );
}
