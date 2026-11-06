import type { PaymentProfile, SecretRef, TransferMethod } from "../../contracts/businessConfig.v1";
import { isLinkActive, isMethodActive } from "./document";
import { BANK_ACCOUNT_TYPES, labelFor, TRANSFER_METHOD_TYPES } from "./options";
import type { BusinessDocument, PaymentFields, PaymentValues } from "./types";

/** `pending`: hay un valor escrito que todavía no se ha guardado. */
export type PaymentDataState = "configured" | "pending" | "missing" | "unreadable";

/** Cómo reconocer un método de pago: lo descriptivo está en el documento y el dato solo llega enmascarado del servidor. */
export interface PaymentMethodSummary {
  /** Su ruta en el documento: identifica la fila. */
  path: string;
  name: string;
  details: string[];
  masked: string | null;
  active: boolean;
  dataState: PaymentDataState;
}

function dataOf(ref: SecretRef | null | undefined, fields: PaymentFields, values: PaymentValues): Pick<PaymentMethodSummary, "masked" | "dataState"> {
  if (!ref) return { masked: null, dataState: "missing" };
  if (values[ref.secret_ref]?.trim()) return { masked: null, dataState: "pending" };
  const field = fields[ref.secret_ref];
  return field ? { masked: field.masked, dataState: field.status } : { masked: null, dataState: "missing" };
}

function methodName(method: TransferMethod): string {
  return method.type === "bank" ? method.bank?.trim() || labelFor(TRANSFER_METHOD_TYPES, "bank") : labelFor(TRANSFER_METHOD_TYPES, method.type);
}

function methodDetails(method: TransferMethod): string[] {
  const accountType = method.type === "bank" && method.account_type ? `Cuenta ${labelFor(BANK_ACCOUNT_TYPES, method.account_type).toLowerCase()}` : null;
  return [accountType, method.label?.trim() || null].filter((detail): detail is string => detail !== null);
}

function methodRef(method: TransferMethod): SecretRef | null | undefined {
  if (method.type === "bank") return method.account_number;
  return method.type === "breb" ? method.reference : method.number;
}

function profileSummaries(profile: PaymentProfile, index: number, several: boolean, fields: PaymentFields, values: PaymentValues): PaymentMethodSummary[] {
  const profileDetail = several ? [`Perfil ${profile.id}`] : [];
  const link: PaymentMethodSummary[] = profile.link
    ? [{ path: `payments.${index}.link`, name: "Enlace de pago", details: profileDetail, active: isLinkActive(profile), ...dataOf(profile.link, fields, values) }]
    : [];
  const methods = (profile.transfer_methods ?? []).map((method, position) => ({
    path: `payments.${index}.transfer_methods.${position}`,
    name: methodName(method),
    details: [...methodDetails(method), ...profileDetail],
    active: isMethodActive(profile, method),
    ...dataOf(methodRef(method), fields, values),
  }));
  return [...link, ...methods];
}

/** Los métodos de pago del negocio, para consultarlos de un vistazo. */
export function summarizePaymentMethods(document: BusinessDocument, fields: PaymentFields, values: PaymentValues): PaymentMethodSummary[] {
  const several = document.payments.length > 1;
  return document.payments.flatMap((profile, index) => profileSummaries(profile, index, several, fields, values));
}
