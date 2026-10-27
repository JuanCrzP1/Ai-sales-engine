import { CheckboxGroup } from "../../components/ui/ChoiceGroup";
import { Alert, Badge } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Layout";
import { Toggle } from "../../components/ui/Toggle";
import { ASSISTANT_ACTIONS, CUSTOMER_DATA_FIELDS } from "../../domain/config/options";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function ClosingForm() {
  const [closing, update] = useSection("closing");
  const methodsIssue = useFieldIssue("closing.methods");
  const paymentIssue = useFieldIssue("closing.sendPaymentLink");
  const handoffIssue = useFieldIssue("closing.humanHandoff");
  const fieldsIssue = useFieldIssue("closing.customerDataFields");
  const actionsIssue = useFieldIssue("closing.actions");

  return (
    <Card title="Cómo se cierra una venta" description="Lo que el asistente puede hacer cuando el cliente está listo.">
      {methodsIssue && <Alert tone="danger">{methodsIssue.message}</Alert>}

      <Toggle
        label="Compartir datos de pago"
        description="Envía el enlace o las cuentas cuando el cliente elige cómo pagar."
        checked={closing.sendPaymentLink}
        onChange={(sendPaymentLink) => update({ sendPaymentLink })}
      />
      {paymentIssue && <p className="field__message field__message--warning">{paymentIssue.message}</p>}

      <Toggle
        label="Ofrecer atención de una persona"
        description="El asistente puede proponer que alguien de tu equipo continúe la conversación."
        checked={closing.humanHandoff}
        onChange={(humanHandoff) => update({ humanHandoff })}
      />
      {handoffIssue && <p className="field__message field__message--warning">{handoffIssue.message}</p>}

      <Toggle
        label="Pedir datos al cliente"
        description="Solo cuando hacen falta para avanzar con la venta."
        checked={closing.collectCustomerData}
        onChange={(collectCustomerData) => update({ collectCustomerData })}
      />
      {closing.collectCustomerData && (
        <CheckboxGroup
          legend="Datos que puede pedir"
          name="customer-data"
          options={CUSTOMER_DATA_FIELDS}
          values={closing.customerDataFields}
          onChange={(customerDataFields) => update({ customerDataFields })}
          issue={fieldsIssue}
        />
      )}

      <CheckboxGroup
        legend="Acciones que puede realizar el asistente"
        hint="Elige las que de verdad aplican a tu negocio."
        name="assistant-actions"
        options={ASSISTANT_ACTIONS.map((action) => ({
          ...action,
          badge: action.primary ? <Badge tone="accent">Venta</Badge> : undefined,
        }))}
        values={closing.actions}
        onChange={(actions) => update({ actions })}
        issue={actionsIssue}
      />
    </Card>
  );
}
