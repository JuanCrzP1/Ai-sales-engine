import { ChatPreview } from "../../components/ui/ChatPreview";
import { TextAreaField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function PaymentMessagesForm() {
  const [messages, update] = useSection("messages");
  const reportedIssue = useFieldIssue("messages.paymentReportedText");

  return (
    <Card
      title="Mensajes de pago"
      description="El asistente no verifica pagos: estos mensajes solo acompañan lo que el cliente informa."
    >
      <div className="grid-2">
        <TextAreaField
          label="Cuando el cliente dice que ya pagó"
          value={messages.paymentReportedText}
          onChange={(paymentReportedText) => update({ paymentReportedText })}
          placeholder="Ej.: Gracias, ya reviso tu pago y te confirmo en un momento."
          issue={reportedIssue}
          hint="Se envía tal cual, sin confirmar el pago."
        />
        <ChatPreview
          caption="Vista previa"
          lines={[
            { from: "customer", text: "Ya te hice la transferencia" },
            { from: "assistant", text: messages.paymentReportedText.trim() || "El asistente responderá con sus propias palabras." },
          ]}
        />
      </div>
      <TextAreaField
        label="Cuando tu equipo confirma el pago"
        value={messages.paymentConfirmedText}
        onChange={(paymentConfirmedText) => update({ paymentConfirmedText })}
        placeholder="Ej.: Listo, tu pago quedó confirmado."
        hint="Referencia para el asistente; la confirmación siempre la hace tu equipo."
      />
    </Card>
  );
}
