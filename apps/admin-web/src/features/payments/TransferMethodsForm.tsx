import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { SelectField, TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { Toggle } from "../../components/ui/Toggle";
import type { TransferMethodDetails } from "../../domain/config/operations";
import { BANK_ACCOUNT_TYPES, labelFor, TRANSFER_METHOD_TYPES } from "../../domain/config/options";
import type { TransferMethod, TransferMethodType } from "../../domain/config/types";
import { issuesFor } from "../../domain/validation/issues";
import type { ValidationIssue } from "../../domain/validation/types";
import { useConfig, useFieldIssue } from "../../state/useConfig";

export function TransferMethodsForm() {
  const { config, issues, actions } = useConfig();
  const listIssue = useFieldIssue("payments.transferMethods");
  const duplicatesIssue = useFieldIssue("payments.transferMethods.duplicates");
  const { transferEnabled, transferMethods: methods } = config.payments;

  return (
    <Card title="Transferencias" description="Cuentas a las que el cliente puede transferir.">
      <Toggle
        label="Aceptar transferencias"
        checked={transferEnabled}
        onChange={(enabled) => actions.updateSection("payments", { transferEnabled: enabled })}
      />

      {transferEnabled && (
        <>
          {listIssue && <Alert tone="warning">{listIssue.message}</Alert>}
          {duplicatesIssue && <Alert tone="warning">{duplicatesIssue.message}</Alert>}
          {methods.length === 0 ? (
            <EmptyState title="No hay cuentas registradas" description="Agrega una cuenta Nequi, Daviplata, bancaria o Bre-B." />
          ) : (
            methods.map((method, index) => (
              <TransferMethodFields
                key={method.id}
                method={method}
                position={index + 1}
                issues={issues}
                onChangeDetails={(details) => actions.updateTransferMethod(method.id, details)}
                onChangeType={(type) => actions.changeTransferMethodType(method.id, type)}
                onRemove={() => actions.removeTransferMethod(method.id)}
              />
            ))
          )}
          <div>
            <Button variant="secondary" onClick={actions.addTransferMethod}>
              Agregar cuenta
            </Button>
          </div>
        </>
      )}
    </Card>
  );
}

interface TransferMethodFieldsProps {
  method: TransferMethod;
  position: number;
  issues: ValidationIssue[];
  onChangeDetails: (details: TransferMethodDetails) => void;
  /** Cambiar el tipo borra los datos del tipo anterior. */
  onChangeType: (type: TransferMethodType) => void;
  onRemove: () => void;
}

function TransferMethodFields({ method, position, issues, onChangeDetails, onChangeType, onRemove }: TransferMethodFieldsProps) {
  const issue = (field: string) => issuesFor(issues, `payments.transfer.${method.id}.${field}`)[0];

  return (
    <fieldset className="subcard">
      <legend className="visually-hidden">Cuenta {position}</legend>
      <div className="card__header">
        <h3 className="field__label">
          Cuenta {position}: {labelFor(TRANSFER_METHOD_TYPES, method.type)}
        </h3>
        <ConfirmButton confirmLabel="Sí, quitar" onConfirm={onRemove}>
          Quitar
        </ConfirmButton>
      </div>
      <div className="grid-2">
        <SelectField
          label="Tipo"
          value={method.type}
          options={TRANSFER_METHOD_TYPES}
          onChange={onChangeType}
          hint="Al cambiar el tipo se borran los datos del tipo anterior."
        />
        {(method.type === "nequi" || method.type === "daviplata") && (
          <TextField
            label="Número de celular"
            type="tel"
            inputMode="tel"
            required
            value={method.phoneNumber}
            onChange={(phoneNumber) => onChangeDetails({ phoneNumber })}
            placeholder="3001234567"
            issue={issue("phoneNumber")}
          />
        )}
        {method.type === "bank" && (
          <>
            <TextField label="Banco" required value={method.bankName} onChange={(bankName) => onChangeDetails({ bankName })} issue={issue("bankName")} />
            <SelectField
              label="Tipo de cuenta"
              value={method.accountType}
              options={BANK_ACCOUNT_TYPES}
              onChange={(accountType) => onChangeDetails({ accountType })}
            />
            <TextField
              label="Número de cuenta"
              inputMode="numeric"
              required
              value={method.accountNumber}
              onChange={(accountNumber) => onChangeDetails({ accountNumber })}
              issue={issue("accountNumber")}
            />
          </>
        )}
        {method.type === "breb" && (
          <TextField
            label="Llave o referencia Bre-B"
            required
            value={method.reference}
            onChange={(reference) => onChangeDetails({ reference })}
            issue={issue("reference")}
          />
        )}
      </div>
    </fieldset>
  );
}
