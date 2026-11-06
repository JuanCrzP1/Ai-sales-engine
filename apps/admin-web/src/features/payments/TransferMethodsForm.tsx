import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, Badge, EmptyState } from "../../components/ui/Feedback";
import { SelectField, TextField } from "../../components/ui/FormFields";
import { Toggle } from "../../components/ui/Toggle";
import { isMethodActive, optionalText } from "../../domain/config/document";
import type { PaymentProfile, TransferMethod } from "../../domain/config/types";
import { BANK_ACCOUNT_TYPES, labelFor, TRANSFER_METHOD_TYPES } from "../../domain/config/options";
import { useConfig, useFieldIssue } from "../../state/useConfig";
import { SecretField } from "./SecretField";

export function TransferMethodsForm({ profile, profileIndex }: { profile: PaymentProfile; profileIndex: number }) {
  const { actions } = useConfig();
  const base = `payments.${profileIndex}.transfer_methods`;
  const listIssue = useFieldIssue(base);
  const duplicatesIssue = useFieldIssue(`${base}.duplicates`);
  const methods = profile.transfer_methods ?? [];

  return (
    <>
      <Toggle label="Aceptar transferencias" checked={profile.transfer_enabled} onChange={(enabled) => actions.setTransferEnabled(profile.id, enabled)} />
      {profile.transfer_enabled && listIssue && <Alert tone="warning">{listIssue.message}</Alert>}
      {profile.transfer_enabled && duplicatesIssue && <Alert tone="warning">{duplicatesIssue.message}</Alert>}
      {!profile.transfer_enabled && methods.length > 0 && <p className="field__hint">Las transferencias están desactivadas: estas cuentas se conservan, pero el asistente no las ofrece.</p>}
      {profile.transfer_enabled && methods.length === 0 && <EmptyState title="No hay cuentas registradas" description="Agrega una cuenta Nequi, Daviplata, bancaria o Bre-B." />}
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

function TransferMethodFields({ method, position, profile, base }: { method: TransferMethod; position: number; profile: PaymentProfile; base: string }) {
  const { actions } = useConfig();
  const profileId = profile.id;
  const path = `${base}.${position}`;
  const bankIssue = useFieldIssue(`${path}.bank`);
  const labelIssue = useFieldIssue(`${path}.label`);
  const active = isMethodActive(profile, method);

  return (
    <fieldset className="subcard">
      <legend className="visually-hidden">Cuenta {position + 1}</legend>
      <div className="card__header">
        <h3 className="field__label">
          Cuenta {position + 1}: {labelFor(TRANSFER_METHOD_TYPES, method.type)} <Badge tone={active ? "success" : "neutral"}>{active ? "Activa" : "Inactiva"}</Badge>
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
          label="Tipo"
          value={method.type}
          options={TRANSFER_METHOD_TYPES}
          onChange={(type) => actions.changeTransferMethodType(profileId, position, type)}
          hint="Al cambiar el tipo se descartan los datos del tipo anterior."
        />
        <TextField
          label="Titular o etiqueta"
          value={method.label ?? ""}
          onChange={(label) => actions.updateTransferMethod(profileId, position, { label: optionalText(label) })}
          issue={labelIssue}
          hint="Para reconocerla aquí. No se comparte con el cliente."
        />
        {method.number && <SecretField label="Número de celular" secretRef={method.number.secret_ref} path={`${path}.number`} type="tel" inputMode="tel" placeholder="3001234567" />}
        {method.type === "bank" && (
          <>
            <TextField label="Banco" required value={method.bank ?? ""} onChange={(bank) => actions.updateTransferMethod(profileId, position, { bank })} issue={bankIssue} />
            <SelectField
              label="Tipo de cuenta"
              value={method.account_type ?? "ahorros"}
              options={BANK_ACCOUNT_TYPES}
              onChange={(account_type) => actions.updateTransferMethod(profileId, position, { account_type })}
            />
          </>
        )}
        {method.account_number && <SecretField label="Número de cuenta" secretRef={method.account_number.secret_ref} path={`${path}.account_number`} inputMode="numeric" />}
        {method.reference && <SecretField label="Llave o referencia Bre-B" secretRef={method.reference.secret_ref} path={`${path}.reference`} />}
      </div>
    </fieldset>
  );
}
