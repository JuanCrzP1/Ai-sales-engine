import { ChatPreview } from "../../components/ui/ChatPreview";
import { TextAreaField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { Toggle } from "../../components/ui/Toggle";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function WelcomeMessageForm() {
  const [messages, update] = useSection("messages");
  const welcome = messages.welcome;
  const textIssue = useFieldIssue("messages.welcome.text");
  const groupIssue = useFieldIssue("messages.welcome");

  return (
    <Card icon="message" tone="violet" title="Mensaje de bienvenida" description="Se envía tal cual cuando un cliente nuevo solo saluda. Si lo desactivas, responde el asistente.">
      <Toggle label="Enviar mensaje de bienvenida" checked={welcome.enabled} onChange={(enabled) => update({ welcome: { ...welcome, enabled } })} />
      {welcome.enabled && (
        <div className="grid-2">
          <TextAreaField
            label="Mensaje"
            required
            rows={4}
            value={welcome.text ?? ""}
            onChange={(text) => update({ welcome: { ...welcome, text } })}
            placeholder="Ej.: ¡Hola! Gracias por escribirnos. ¿En qué te ayudo?"
            issue={textIssue ?? groupIssue}
          />
          <ChatPreview
            caption="Vista previa"
            lines={[
              { from: "customer", text: "Hola" },
              { from: "assistant", text: welcome.text?.trim() || "Escribe tu mensaje para verlo aquí." },
            ]}
          />
        </div>
      )}
    </Card>
  );
}
