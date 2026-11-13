import { MAX_PAYMENT_INSTRUCTIONS_CHARS, PAYMENT_METHOD_CATALOG, type TransferMethod } from "../../contracts/businessConfig.v1";

/** Lo más largo de la instrucción de un medio de pago. */
export { MAX_PAYMENT_INSTRUCTIONS_CHARS };

/**
 * Los medios de pago que un negocio puede configurar, de cualquier país. Llegan generados desde el servidor
 * (`project/app/domain/business_config/payment_catalog.py`): aquí solo se leen. Cada medio dice su nombre, su país, qué dato pide
 * (y en cuál casilla cifrada va), cómo se valida y cómo sale en el mensaje al cliente.
 */
export type PaymentMethodKind = (typeof PAYMENT_METHOD_CATALOG)[number];
export type PaymentMethodId = PaymentMethodKind["id"];
export type PaymentDataFormat = "mobile" | "phone" | "account" | "clabe" | "iban" | "email" | "reference";
export type PaymentSlot = "number" | "account_number" | "reference";

const BY_ID = new Map<string, PaymentMethodKind>(PAYMENT_METHOD_CATALOG.map((kind) => [kind.id, kind]));

export function methodKind(id: string): PaymentMethodKind | undefined {
  return BY_ID.get(id);
}

/** El dato que pide un medio (o null: el efectivo no pide datos). */
export function dataFieldOf(id: string): { slot: PaymentSlot; label: string; format: PaymentDataFormat; placeholder: string; shownAs: string } | null {
  const data = methodKind(id)?.data;
  return data ? { slot: data.slot as PaymentSlot, label: data.label, format: data.format as PaymentDataFormat, placeholder: data.placeholder, shownAs: data.shownAs } : null;
}

/** Cómo se valida el dato guardado en una casilla de un medio. */
export function formatOf(id: string, slot: PaymentSlot): PaymentDataFormat {
  const data = dataFieldOf(id);
  return data && data.slot === slot ? data.format : "reference";
}

/** El nombre de una cuenta como la reconoce el negocio: el banco, el nombre de «otro medio» o el del medio. */
export function methodName(method: Pick<TransferMethod, "type" | "bank" | "name">): string {
  const kind = methodKind(method.type);
  if (kind?.needsBank && method.bank?.trim()) return method.bank.trim();
  if (kind?.custom && method.name?.trim()) return method.name.trim();
  return kind?.name ?? method.type;
}
