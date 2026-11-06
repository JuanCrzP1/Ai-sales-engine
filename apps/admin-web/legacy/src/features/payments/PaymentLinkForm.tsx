import { TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { Toggle } from "../../components/ui/Toggle";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function PaymentLinkForm() {
  const [payments, update] = useSection("payments");
  const linkIssue = useFieldIssue("payments.paymentLink");

  return (
    <Card title="Enlace de pago" description="Un enlace de tu pasarela de pagos (Wompi, Mercado Pago, PayU u otra).">
      <Toggle
        label="Ofrecer pago por enlace"
        checked={payments.paymentLinkEnabled}
        onChange={(paymentLinkEnabled) => update({ paymentLinkEnabled })}
      />
      {payments.paymentLinkEnabled && (
        <TextField
          label="Enlace de pago"
          type="url"
          inputMode="url"
          required
          value={payments.paymentLink}
          onChange={(paymentLink) => update({ paymentLink })}
          placeholder="https://"
          issue={linkIssue}
          hint="El asistente usa un único enlace para todas las compras."
        />
      )}
    </Card>
  );
}
