import { ChatPreview } from "../../components/ui/ChatPreview";
import { TextAreaField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { Toggle } from "../../components/ui/Toggle";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function WelcomeMessageForm() {
  const [messages, update] = useSection("messages");
  const welcomeIssue = useFieldIssue("messages.welcomeText");

  return (
    <Card title="Mensaje de bienvenida" description="Se envía tal cual cuando un cliente nuevo solo saluda.">
      <Toggle
        label="Enviar mensaje de bienvenida"
        checked={messages.welcomeEnabled}
        onChange={(welcomeEnabled) => update({ welcomeEnabled })}
      />
      {messages.welcomeEnabled && (
        <div className="grid-2">
          <TextAreaField
            label="Mensaje"
            required
            rows={4}
            value={messages.welcomeText}
            onChange={(welcomeText) => update({ welcomeText })}
            placeholder="Ej.: ¡Hola! Gracias por escribirnos. ¿En qué te ayudo?"
            issue={welcomeIssue}
          />
          <ChatPreview
            caption="Vista previa"
            lines={[
              { from: "customer", text: "Hola" },
              { from: "assistant", text: messages.welcomeText.trim() || "Escribe tu mensaje para verlo aquí." },
            ]}
          />
        </div>
      )}
    </Card>
  );
}
