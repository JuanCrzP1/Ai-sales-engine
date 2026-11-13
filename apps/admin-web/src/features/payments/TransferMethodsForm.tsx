import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, Badge, EmptyState } from "../../components/ui/Feedback";
import { SelectField, TextAreaField, TextField } from "../../components/ui/FormFields";
import { Toggle } from "../../components/ui/Toggle";
import { isMethodActive, optionalText } from "../../domain/config/document";
import type { PaymentProfile, TransferMethod } from "../../domain/config/types";
import { BANK_ACCOUNT_TYPES, TRANSFER_METHOD_TYPES } from "../../domain/config/options";
import { dataFieldOf, MAX_PAYMENT_INSTRUCTIONS_CHARS, methodKind, methodName } from "../../domain/config/paymentCatalog";
import { useConfig, useFieldIssue } from "../../state/useConfig";
import { SecretField } from "./SecretField";

export function TransferMethodsForm({ profile, profileIndex }: { profile: PaymentProfile; profileIndex: number }) {
  const { actions } = useConfig();
  const base = `payments.${profileIndex}.transfer_methods`;
  const listIssue = useFieldIssue(base);
  const methods = profile.transfer_methods ?? [];

  return (
    <>
      <Toggle label="Aceptar transferencias" checked={profile.transfer_enabled} onChange={(enabled) => actions.setTransferEnabled(profile.id, enabled)} />
      {profile.transfer_enabled && listIssue && <Alert tone="warning">{listIssue.message}</Alert>}
      {!profile.transfer_enabled && methods.length > 0 && <p className="field__hint">Las transferencias están desactivadas: estas cuentas se conservan, pero el asistente no las ofrece.</p>}
      {profile.transfer_enabled && methods.length === 0 && <EmptyState title="No hay cuentas registradas" description="Agrega los medios con los que te pagan: Nequi, Yape, una cuenta bancaria, PayPal, efectivo u otro medio." />}
      {methods.map((method, index) => (
        <TransferMethodFields key={index} method={method} position={index} profile={profile} base={base} />
      ))}
      {profile.transfer_enabled && (
        <div>
          <Button variant="secondary" onClick={() => actions.addTransferMethod(profile.id)}>
            Agregar cuenta
          </Button>
        </div>
      )}
    </>
  );
}

/** Cómo se escribe el dato en el celular: teclado de números para cuentas, de teléfono para celulares. */
function keyboardFor(format: string): { type: "text" | "tel"; inputMode: "text" | "numeric" | "tel" } {
  if (format === "mobile" || format === "phone") return { type: "tel", inputMode: "tel" };
  if (format === "account" || format === "clabe") return { type: "text", inputMode: "numeric" };
  return { type: "text", inputMode: "text" };
}

function TransferMethodFields({ method, position, profile, base }: { method: TransferMethod; position: number; profile: PaymentProfile; base: string }) {
  const { actions } = useConfig();
  const profileId = profile.id;
  const path = `${base}.${position}`;
  const bankIssue = useFieldIssue(`${path}.bank`);
  const nameIssue = useFieldIssue(`${path}.name`);
  const labelIssue = useFieldIssue(`${path}.label`);
  const holderIssue = useFieldIssue(`${path}.holder`);
  const instructionsIssue = useFieldIssue(`${path}.instructions`);
  const active = isMethodActive(profile, method);
  const kind = methodKind(method.type);
  const data = dataFieldOf(method.type);
  const ref = data ? method[data.slot] : null;
  const update = (patch: Parameters<typeof actions.updateTransferMethod>[2]) => actions.updateTransferMethod(profileId, position, patch);

  return (
    <fieldset className="subcard">
      <legend className="visually-hidden">Cuenta {position + 1}</legend>
      <div className="card__header">
        <h3 className="field__label">
          Cuenta {position + 1}: {methodName(method)} <Badge tone={active ? "success" : "neutral"}>{active ? "Activa" : "Inactiva"}</Badge>
        </h3>
        <ConfirmButton confirmLabel="Sí, quitar" onConfirm={() => actions.removeTransferMethod(profileId, position)}>
          Quitar
        </ConfirmButton>
      </div>
      <Toggle
        label="Cuenta activa"
        description="Una cuenta inactiva conserva sus datos, pero el asistente no la ofrece."
        checked={method.enabled !== false}
        onChange={(enabled) => actions.setTransferMethodEnabled(profileId, position, enabled)}
      />
      <div className="grid-2">
        <SelectField
          label="Medio de pago"
          value={method.type}
          options={TRANSFER_METHOD_TYPES}
          onChange={(type) => actions.changeTransferMethodType(profileId, position, type)}
          hint="Elige el de tu país, o «Otro medio» si no está. Al cambiarlo se descarta el dato anterior."
        />
        {kind?.custom && (
          <>
            <TextField label="Nombre del medio" required value={method.name ?? ""} placeholder="Ej.: Nu, Ualá, Western Union" onChange={(name) => update({ name })} issue={nameIssue} hint="Así lo verá el cliente." />
            <TextField
              label="Cómo se llama el dato"
              value={method.data_label ?? ""}
              placeholder="Ej.: Número de cuenta, Alias"
              onChange={(label) => update({ data_label: optionalText(label) })}
              hint="Sale antes del dato en el mensaje. Si lo dejas vacío, sale solo el dato."
            />
          </>
        )}
        {kind?.needsBank && (
          <>
            <TextField label="Banco" required value={method.bank ?? ""} onChange={(bank) => update({ bank })} issue={bankIssue} />
            <SelectField label="Tipo de cuenta" value={method.account_type ?? "ahorros"} options={BANK_ACCOUNT_TYPES} onChange={(account_type) => update({ account_type })} />
          </>
        )}
        {data && ref && (
          <SecretField
            label={kind?.custom ? method.data_label?.trim() || data.label : data.label}
            secretRef={ref.secret_ref}
            path={`${path}.${data.slot}`}
            placeholder={data.placeholder || undefined}
            {...keyboardFor(data.format)}
          />
        )}
        {data && (
          <TextField
            label="A nombre de"
            value={method.holder ?? ""}
            placeholder="Ej.: Café Aroma S.A.S."
            onChange={(holder) => update({ holder: optionalText(holder) })}
            issue={holderIssue}
            hint="El cliente lo ve con los datos de pago, para que sepa que le paga a tu negocio."
          />
        )}
        <TextField
          label="Etiqueta (solo para ti)"
          value={method.label ?? ""}
          onChange={(label) => update({ label: optionalText(label) })}
          issue={labelIssue}
          hint="Para reconocer la cuenta aquí. No se comparte con el cliente."
        />
      </div>
      <TextAreaField
        label={data ? "Instrucción para el cliente (opcional)" : "Qué debe saber el cliente"}
        value={method.instructions ?? ""}
        rows={2}
        maxLength={MAX_PAYMENT_INSTRUCTIONS_CHARS}
        placeholder={data ? "Ej.: Envía la captura del comprobante con tu nombre." : "Ej.: Pagas al domiciliario cuando recibes tu pedido."}
        onChange={(instructions) => update({ instructions: optionalText(instructions) })}
        issue={instructionsIssue}
        hint="Sale con los datos de pago, tal cual. La IA no la ve."
      />
    </fieldset>
  );
}
