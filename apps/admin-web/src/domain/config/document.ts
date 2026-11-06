import type { CatalogItem, PaymentProfile, Plan, SecretRef, TransferMethod } from "../../contracts/businessConfig.v1";
import { cleanList } from "../../lib/text";
import type { BusinessDocument, PaymentValues, WorkingCopy } from "./types";

/** Lecturas puras del documento. */

export type OfferEntry = Plan | CatalogItem;

export function isCatalog(document: BusinessDocument): boolean {
  return document.offer.model === "catalog";
}

export function offerEntries(document: BusinessDocument): OfferEntry[] {
  return isCatalog(document) ? (document.offer.catalog?.items ?? []) : (document.offer.plans ?? []);
}

export function isAvailable(entry: OfferEntry): boolean {
  return entry.available !== false;
}

export function categoryName(document: BusinessDocument, id: string): string {
  return document.offer.catalog?.categories.find((category) => category.id === id)?.name ?? id;
}

/** Texto opcional del contrato: en blanco significa que no se indica. */
export function optionalText(value: string): string | null {
  return value.trim() ? value : null;
}

/** Lista opcional del contrato: vacía significa que no se indica. */
export function optionalList<T>(items: T[]): T[] | null {
  return items.length > 0 ? items : null;
}

/** Forma comparable: sin vacíos opcionales y con las claves ordenadas. */
function comparable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(comparable);
  if (value !== null && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>)
      .filter(([, item]) => item !== null && item !== undefined)
      .sort(([a], [b]) => a.localeCompare(b));
    return Object.fromEntries(entries.map(([key, item]) => [key, comparable(item)]));
  }
  return value;
}

export function sameDocument(a: BusinessDocument, b: BusinessDocument): boolean {
  return JSON.stringify(comparable(a)) === JSON.stringify(comparable(b));
}

/** Un dato de pago dentro del documento, con la ruta y el tipo que determinan cómo se escribe. */
export interface PaymentHolder {
  path: string;
  kind: "link" | "mobile" | "account" | "reference";
  ref: SecretRef;
}

function transferHolders(path: string, method: TransferMethod): PaymentHolder[] {
  const holders: PaymentHolder[] = [];
  if (method.number) holders.push({ path: `${path}.number`, kind: "mobile", ref: method.number });
  if (method.account_number) holders.push({ path: `${path}.account_number`, kind: "account", ref: method.account_number });
  if (method.reference) holders.push({ path: `${path}.reference`, kind: "reference", ref: method.reference });
  return holders;
}

export function paymentHolders(payments: PaymentProfile[]): PaymentHolder[] {
  return payments.flatMap((profile, profileIndex) => {
    const base = `payments.${profileIndex}`;
    return [
      ...(profile.link ? [{ path: `${base}.link`, kind: "link" as const, ref: profile.link }] : []),
      ...(profile.transfer_methods ?? []).flatMap((method, methodIndex) => transferHolders(`${base}.transfer_methods.${methodIndex}`, method)),
    ];
  });
}

/**
 * Los valores tal como se envían: sin espacios sobrantes y solo los que siguen en el documento. Un dato ya guardado con el
 * campo de reemplazo vacío no se envía: el reemplazo es explícito, y sin un valor nuevo se conserva el que hay.
 */
export function paymentValuesToSend({ document, paymentValues }: WorkingCopy): PaymentValues {
  const values: PaymentValues = {};
  for (const holder of paymentHolders(document.payments)) {
    const value = paymentValues[holder.ref.secret_ref];
    if (value === undefined || (isStoredRef(holder.ref.secret_ref) && !value.trim())) continue;
    values[holder.ref.secret_ref] = holder.kind === "mobile" ? value.replace(/\s+/g, "") : holder.kind === "account" ? value.replace(/[\s-]+/g, "") : value.trim();
  }
  return values;
}

/** Un dato ya guardado: el servidor añade `~<versión>` a la referencia al cifrarlo. */
export function isStoredRef(ref: string): boolean {
  return ref.includes("~");
}

/** Un enlace inactivo se conserva, pero no se ofrece. */
export function isLinkActive(profile: PaymentProfile): boolean {
  return Boolean(profile.link) && profile.link_enabled !== false;
}

/** Una cuenta se ofrece si está activa y su perfil acepta transferencias. */
export function isMethodActive(profile: PaymentProfile, method: TransferMethod): boolean {
  return profile.transfer_enabled && method.enabled !== false;
}

/** Cuántos medios de pago se ofrecen y cuántos se conservan sin ofrecerse. */
export function paymentOptionCounts(document: BusinessDocument): { active: number; inactive: number } {
  const counts = { active: 0, inactive: 0 };
  for (const profile of document.payments) {
    if (profile.link) counts[isLinkActive(profile) ? "active" : "inactive"] += 1;
    for (const method of profile.transfer_methods ?? []) counts[isMethodActive(profile, method) ? "active" : "inactive"] += 1;
  }
  return counts;
}

/** Medios de pago que el asistente puede ofrecer. */
export function paymentOptionsCount(document: BusinessDocument): number {
  return paymentOptionCounts(document).active;
}

/** Acciones del negocio, de venta y de apoyo, sin distinguir la lista en la que están. */
export function allActions(document: BusinessDocument): string[] {
  const { actions_primary: primary = [], actions_support: support = [] } = document.capabilities;
  return [...primary, ...support];
}

export function joinList(items: string[] | null | undefined): string {
  return cleanList(items ?? []).join(" · ");
}
