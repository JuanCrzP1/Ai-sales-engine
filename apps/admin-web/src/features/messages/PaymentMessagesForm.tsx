import { ChatPreview } from "../../components/ui/ChatPreview";
import { TextAreaField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { optionalText } from "../../domain/config/document";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function PaymentMessagesForm() {
  const [messages, update] = useSection("messages");
  const reportedIssue = useFieldIssue("messages.payment_reported");
  const confirmedIssue = useFieldIssue("messages.payment_confirmed");

  return (
    <Card title="Mensajes de pago" description="El asistente no verifica pagos: estos mensajes solo acompañan lo que el cliente informa.">
      <div className="grid-2">
        <TextAreaField
          label="Cuando el cliente dice que ya pagó"
          value={messages.payment_reported ?? ""}
          onChange={(text) => update({ payment_reported: optionalText(text) })}
          placeholder="Ej.: Gracias, ya reviso tu pago y te confirmo en un momento."
          issue={reportedIssue}
          hint="Se envía tal cual, sin confirmar el pago."
        />
        <ChatPreview
          caption="Vista previa"
          lines={[
            { from: "customer", text: "Ya te hice la transferencia" },
            { from: "assistant", text: messages.payment_reported?.trim() || "El asistente responderá con sus propias palabras." },
          ]}
        />
      </div>
      <TextAreaField
        label="Cuando tu equipo confirma el pago"
        value={messages.payment_confirmed ?? ""}
        onChange={(text) => update({ payment_confirmed: optionalText(text) })}
        placeholder="Ej.: Listo, tu pago quedó confirmado."
        issue={confirmedIssue}
        hint="Se guarda para cuando tu equipo pueda confirmar pagos desde el panel: entonces se enviará al cliente. El asistente nunca confirma pagos."
      />
    </Card>
  );
}
