import { ChatPreview } from "../../components/ui/ChatPreview";
import { TextAreaField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { PLATFORM_FALLBACK_REPLY } from "../../domain/assistant/fallback";
import { optionalText } from "../../domain/config/document";
import { useFieldIssue, useSection } from "../../state/useConfig";

/** El mensaje que reciben los clientes si la IA no puede responder (sin clave, sin saldo o con el proveedor caído). */
export function FallbackMessageForm() {
  const [messages, update] = useSection("messages");
  const issue = useFieldIssue("messages.fallback");

  return (
    <Card
      icon="alert"
      tone="amber"
      wide
      title="Si el asistente no puede responder"
      description="Se envía tal cual cuando la IA falla: por ejemplo, si tu clave de OpenRouter se queda sin saldo o el proveedor no responde."
    >
      <div className="grid-2">
        <TextAreaField
          label="Lo que recibe el cliente"
          value={messages.fallback ?? ""}
          onChange={(text) => update({ fallback: optionalText(text) })}
          placeholder="Ej.: En este momento no podemos responder por aquí. Escríbenos al 300 123 4567 o vuelve en un rato."
          issue={issue}
          hint="Escríbelo como tu negocio: con tu horario o un teléfono de contacto. Si lo dejas vacío, se envía el mensaje que ves en la vista previa."
        />
        <ChatPreview
          caption="Vista previa"
          lines={[
            { from: "customer", text: "¿Tienen disponibilidad para mañana?" },
            { from: "assistant", text: messages.fallback?.trim() || PLATFORM_FALLBACK_REPLY },
          ]}
        />
      </div>
    </Card>
  );
}
