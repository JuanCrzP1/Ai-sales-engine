import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { isStoredRef } from "../../domain/config/document";
import type { PaymentFieldState } from "../../domain/config/types";
import { useConfig, useFieldIssue } from "../../state/useConfig";

interface SecretFieldProps {
  label: string;
  /** Referencia del dato en el documento. */
  secretRef: string;
  /** Ruta del dato en el documento, para mostrar sus errores. */
  path: string;
  placeholder?: string;
  type?: "text" | "url" | "tel";
  inputMode?: "text" | "numeric" | "tel" | "url";
  hint?: string;
}

function StoredState({ field }: { field: PaymentFieldState | undefined }) {
  if (field?.status === "configured") {
    return (
      <>
        <Badge tone="success">Guardado de forma segura</Badge>
        {field.masked && <code className="secret-mask">{field.masked}</code>}
      </>
    );
  }
  if (field?.status === "unreadable") return <Badge tone="danger">No se puede leer con la clave actual</Badge>;
  return <Badge tone="danger">Falta este dato</Badge>;
}

/**
 * Dato de pago: el valor guardado nunca llega al navegador, solo una versión enmascarada para reconocerlo. No se puede editar,
 * solo reemplazar, y mientras no se escriba uno nuevo se conserva el que hay. Lo que se escribe aquí se envía una vez al
 * guardar y el servidor lo cifra.
 */
export function SecretField({ label, secretRef, path, placeholder, type = "text", inputMode, hint }: SecretFieldProps) {
  const { paymentValues, paymentFields, actions } = useConfig();
  const issue = useFieldIssue(path);
  const value = paymentValues[secretRef];
  const stored = isStoredRef(secretRef);
  const field = paymentFields[secretRef];

  if (value === undefined) {
    return (
      <div className="field">
        <p className="field__label">{label}</p>
        <p className="secret-stored">
          <StoredState field={field} />
          <Button variant="ghost" size="small" onClick={() => actions.setPaymentValue(secretRef, "")} aria-label={`Reemplazar ${label}`}>
            Reemplazar
          </Button>
        </p>
      </div>
    );
  }

  const usable = stored && field?.status === "configured";
  return (
    <div className="secret-input">
      <TextField
        label={label}
        required={!stored}
        type={type}
        inputMode={inputMode}
        value={value}
        onChange={(next) => actions.setPaymentValue(secretRef, next)}
        placeholder={placeholder}
        issue={issue}
        hint={usable ? `Si lo dejas vacío, se conserva el dato guardado${field.masked ? ` (${field.masked})` : ""}.` : hint}
      />
      {stored && (
        <Button variant="ghost" size="small" onClick={() => actions.keepStoredPaymentValue(secretRef)}>
          {usable ? "Conservar el dato guardado" : "Cancelar"}
        </Button>
      )}
    </div>
  );
}
