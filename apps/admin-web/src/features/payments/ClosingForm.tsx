import { CheckboxGroup } from "../../components/ui/ChoiceGroup";
import { Alert, Badge } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Layout";
import { Toggle } from "../../components/ui/Toggle";
import { ASSISTANT_ACTIONS, CUSTOMER_DATA_FIELDS, isPrimaryAction, withCurrentValues } from "../../domain/config/options";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function ClosingForm() {
  const [capabilities, update] = useSection("capabilities");
  const methods = capabilities.closing_methods;
  const collection = capabilities.data_collection;
  const primary = capabilities.actions_primary ?? [];
  const support = capabilities.actions_support ?? [];
  const actions = [...primary, ...support];
  const methodsIssue = useFieldIssue("capabilities.closing_methods");
  const paymentIssue = useFieldIssue("capabilities.closing_methods.payment_link");
  const handoffIssue = useFieldIssue("capabilities.closing_methods.human_handoff");
  const fieldsIssue = useFieldIssue("capabilities.data_collection");
  const actionsIssue = useFieldIssue("capabilities.actions");

  /** Una acción se queda en la lista donde estaba; las nuevas van a la que les corresponde. */
  const changeActions = (next: string[]) => {
    const inPrimary = (action: string) => primary.includes(action) || (!support.includes(action) && isPrimaryAction(action));
    update({ actions_primary: next.filter(inPrimary), actions_support: next.filter((action) => !inPrimary(action)) });
  };

  return (
    <Card title="Cómo se cierra una venta" description="Lo que el asistente puede hacer cuando el cliente está listo.">
      {methodsIssue && <Alert tone="danger">{methodsIssue.message}</Alert>}

      <Toggle
        label="Compartir datos de pago"
        description="Envía el enlace o las cuentas cuando el cliente elige cómo pagar."
        checked={methods.payment_link}
        onChange={(payment_link) => update({ closing_methods: { ...methods, payment_link } })}
      />
      {paymentIssue && <p className="field__message field__message--warning">{paymentIssue.message}</p>}

      <Toggle
        label="Ofrecer atención de una persona"
        description="El asistente puede proponer que alguien de tu equipo continúe la conversación."
        checked={methods.human_handoff}
        onChange={(human_handoff) => update({ closing_methods: { ...methods, human_handoff } })}
      />
      {handoffIssue && <p className="field__message field__message--warning">{handoffIssue.message}</p>}

      <Toggle
        label="Pedir datos al cliente"
        description="Solo cuando hacen falta para avanzar con la venta."
        checked={methods.data_collection}
        onChange={(data_collection) => update({ closing_methods: { ...methods, data_collection }, data_collection: { ...collection, enabled: data_collection } })}
      />
      {collection.enabled && (
        <CheckboxGroup
          legend="Datos que puede pedir"
          name="customer-data"
          options={withCurrentValues(CUSTOMER_DATA_FIELDS, collection.fields ?? [])}
          values={collection.fields ?? []}
          onChange={(fields) => update({ data_collection: { ...collection, fields } })}
          issue={fieldsIssue}
        />
      )}

      <CheckboxGroup
        legend="Acciones que puede realizar el asistente"
        hint="Elige las que de verdad aplican a tu negocio."
        name="assistant-actions"
        options={withCurrentValues(ASSISTANT_ACTIONS, actions).map((action) => ({
          ...action,
          badge: "primary" in action && action.primary ? <Badge tone="accent">Venta</Badge> : undefined,
        }))}
        values={actions}
        onChange={changeActions}
        issue={actionsIssue}
      />
    </Card>
  );
}
