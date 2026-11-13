import { useState } from "react";
import { Button } from "../../components/ui/Button";
import { ChatPreview } from "../../components/ui/ChatPreview";
import { TextAreaField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { isMethodActive, optionalText } from "../../domain/config/document";
import { labelFor, TRANSFER_METHOD_TYPES } from "../../domain/config/options";
import { ACCOUNT_TYPE_TEXT, DEFAULT_PAYMENT_DETAILS, renderPaymentDetails } from "../../domain/config/paymentMessage";
import type { BusinessDocument } from "../../domain/config/types";
import { useConfig, useFieldIssue, useSection } from "../../state/useConfig";

/** Datos de ejemplo para la vista previa: los reales están cifrados y nunca llegan al panel. */
function sampleFor(document: BusinessDocument): { medio: string; datos: string; titular: string } {
  for (const profile of document.payments ?? []) {
    const method = (profile.transfer_methods ?? []).find((item) => profile.transfer_enabled && isMethodActive(profile, item));
    if (!method) continue;
    const titular = method.holder ?? "";
    if (method.type === "bank") {
      return { medio: method.bank || "Tu banco", datos: `${ACCOUNT_TYPE_TEXT[method.account_type ?? "ahorros"] ?? "Cuenta"}\n1234567890`, titular };
    }
    if (method.type === "breb") return { medio: "Bre-B", datos: "Llave: @tunegocio", titular };
    return { medio: labelFor(TRANSFER_METHOD_TYPES, method.type), datos: "3001234567", titular };
  }
  return { medio: "Nequi", datos: "3001234567", titular: document.identity.name };
}

export function PaymentMessagesForm() {
  const { document } = useConfig();
  const [messages, update] = useSection("messages");
  const detailsIssue = useFieldIssue("messages.payment_details");
  const reportedIssue = useFieldIssue("messages.payment_reported");
  const confirmedIssue = useFieldIssue("messages.payment_confirmed");
  // Lo que se ve en el campo: mientras se escribe puede quedar vacío (entonces se usa el recomendado), sin que el texto vuelva solo.
  const [details, setDetails] = useState(messages.payment_details ?? DEFAULT_PAYMENT_DETAILS);
  const custom = Boolean(messages.payment_details);
  const changeDetails = (text: string) => {
    setDetails(text);
    update({ payment_details: text.trim() === DEFAULT_PAYMENT_DETAILS ? null : optionalText(text) });
  };

  return (
    <Card icon="wallet" tone="emerald" title="Mensajes de pago" description="El asistente no verifica pagos: estos mensajes solo acompañan lo que el cliente informa.">
      <div className="grid-2">
        <div className="form-stack">
          <TextAreaField
            label="Cómo le llegan los datos de pago"
            value={details}
            rows={8}
            onChange={changeDetails}
            issue={detailsIssue}
            hint="Lo envía el sistema cuando el cliente elige cómo pagar, con los datos reales: la IA nunca los ve. Usa {medio} (Nequi, tu banco…), {datos} (el número o la cuenta, obligatorio) y {titular} (a nombre de quién está). Una línea con un dato vacío no se envía. Si lo dejas vacío, se usa el recomendado."
          />
          {(custom || details !== DEFAULT_PAYMENT_DETAILS) && (
            <div>
              <Button size="small" variant="ghost" onClick={() => changeDetails(DEFAULT_PAYMENT_DETAILS)}>
                Volver al mensaje recomendado
              </Button>
            </div>
          )}
        </div>
        <ChatPreview
          caption="Vista previa con datos de ejemplo"
          lines={[
            { from: "customer", text: "Quiero pagar por transferencia" },
            { from: "assistant", text: renderPaymentDetails(messages.payment_details, sampleFor(document)) },
          ]}
        />
      </div>
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
