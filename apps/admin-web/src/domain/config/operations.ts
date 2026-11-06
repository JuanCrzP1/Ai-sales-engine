import type { CatalogItem, Plan, PlanPrice, TransferMethod } from "../../contracts/businessConfig.v1";
import { categoryId, newSecretRef } from "./factories";
import { isCatalog, isStoredRef, paymentHolders } from "./document";
import type { BusinessDocument, EditableSection, OfferModel, PaymentValues, TransferMethodType, WorkingCopy } from "./types";

/**
 * Operaciones puras sobre lo que se está editando: reciben el documento y devuelven uno nuevo, sin mutar el original.
 * Son la única forma de modificarlo desde la interfaz (a través de `useConfigActions`).
 */

export function updateSection<K extends EditableSection>(document: BusinessDocument, section: K, patch: Partial<BusinessDocument[K]>): BusinessDocument {
  return { ...document, [section]: { ...(document[section] as object), ...patch } };
}

/** Reemplaza una sección completa (la que edita el formulario generado desde el contrato). */
export function setRootValue(document: BusinessDocument, key: keyof BusinessDocument, value: unknown): BusinessDocument {
  return { ...document, [key]: value };
}

// --------------------------------------------------------------------------- oferta

function withPlans(document: BusinessDocument, plans: Plan[]): BusinessDocument {
  return { ...document, offer: { ...document.offer, plans } };
}

function withCatalog(document: BusinessDocument, change: (catalog: NonNullable<BusinessDocument["offer"]["catalog"]>) => NonNullable<BusinessDocument["offer"]["catalog"]>): BusinessDocument {
  const catalog = document.offer.catalog ?? { categories: [], items: [] };
  return { ...document, offer: { ...document.offer, catalog: change(catalog) } };
}

/** Agrega el plan, o lo reemplaza si ya existe uno con el mismo id. */
export function savePlan(document: BusinessDocument, plan: Plan): BusinessDocument {
  const plans = document.offer.plans ?? [];
  return withPlans(document, plans.some((item) => item.id === plan.id) ? plans.map((item) => (item.id === plan.id ? plan : item)) : [...plans, plan]);
}

/** Agrega o reemplaza el producto; la categoría se indica por nombre y se crea si es nueva. */
export function saveCatalogItem(document: BusinessDocument, item: CatalogItem, category: string): BusinessDocument {
  return withCatalog(document, (catalog) => {
    const name = category.trim() || "General";
    const existing = catalog.categories.find((entry) => entry.name.trim().toLowerCase() === name.toLowerCase() || entry.id === categoryId(name));
    const id = existing?.id ?? categoryId(name);
    const saved = { ...item, category: id };
    return {
      ...catalog,
      categories: existing ? catalog.categories : [...catalog.categories, { id, name }],
      items: catalog.items.some((entry) => entry.id === item.id) ? catalog.items.map((entry) => (entry.id === item.id ? saved : entry)) : [...catalog.items, saved],
      payment_profile: catalog.payment_profile ?? document.payments[0]?.id ?? null,
    };
  });
}

/** Quita el plan o producto. Sus variantes de inventario se van con él: sin producto serían inválidas. */
export function removeEntry(document: BusinessDocument, id: string): BusinessDocument {
  if (!isCatalog(document)) return withPlans(document, (document.offer.plans ?? []).filter((plan) => plan.id !== id));
  const next = withCatalog(document, (catalog) => ({ ...catalog, items: catalog.items.filter((item) => item.id !== id) }));
  return { ...next, inventory: { ...next.inventory, items: (next.inventory.items ?? []).filter((entry) => entry.product_id !== id) } };
}

export function setEntryAvailability(document: BusinessDocument, id: string, available: boolean): BusinessDocument {
  if (!isCatalog(document)) return withPlans(document, (document.offer.plans ?? []).map((plan) => (plan.id === id ? { ...plan, available } : plan)));
  return withCatalog(document, (catalog) => ({ ...catalog, items: catalog.items.map((item) => (item.id === id ? { ...item, available } : item)) }));
}

export function renameCategory(document: BusinessDocument, id: string, name: string): BusinessDocument {
  return withCatalog(document, (catalog) => ({ ...catalog, categories: catalog.categories.map((category) => (category.id === id ? { ...category, name } : category)) }));
}

export function removeCategory(document: BusinessDocument, id: string): BusinessDocument {
  return withCatalog(document, (catalog) => ({ ...catalog, categories: catalog.categories.filter((category) => category.id !== id) }));
}

function firstPlanAmount(price: PlanPrice): number {
  return price.price ?? price.monthly ?? price.annual ?? price.implementation ?? price.first_payment ?? 0;
}

/**
 * Cambia la forma de venta. El contrato no admite planes y catálogo a la vez, así que lo que no existe en la otra
 * forma se pierde (lo que no incluye, costos iniciales, variantes): la interfaz lo avisa antes de confirmar.
 */
export function switchOfferModel(document: BusinessDocument, model: OfferModel): BusinessDocument {
  if (document.offer.model === model) return document;
  if (model === "catalog") {
    const plans = document.offer.plans ?? [];
    const items: CatalogItem[] = plans.map((plan) => ({
      id: plan.id,
      name: plan.name,
      category: "general",
      description: plan.description ?? null,
      prices: plan.prices.map((price) => ({ currency: price.currency, amount: firstPlanAmount(price) })),
      features: plan.includes ?? null,
      available: plan.available !== false,
    }));
    return {
      ...document,
      offer: {
        model: "catalog",
        catalog: {
          categories: items.length > 0 ? [{ id: "general", name: "General" }] : [],
          items,
          payment_profile: plans[0]?.payment_profile ?? document.payments[0]?.id ?? null,
        },
      },
    };
  }
  const catalog = document.offer.catalog;
  const plans: Plan[] = (catalog?.items ?? []).map((item) => ({
    id: item.id,
    name: item.name,
    description: item.description ?? null,
    prices: item.prices.map((price) => ({ currency: price.currency, price: price.amount })),
    includes: item.features ?? null,
    not_included: [],
    payment_profile: catalog?.payment_profile ?? null,
    available: item.available !== false,
  }));
  return { ...document, offer: { model: "plans", plans }, inventory: { ...document.inventory, items: [] } };
}

// --------------------------------------------------------------------------- datos de pago

function withoutValues(values: PaymentValues, refs: string[]): PaymentValues {
  const next = { ...values };
  for (const ref of refs) delete next[ref];
  return next;
}

function refsOfMethod(method: TransferMethod): string[] {
  return [method.number, method.account_number, method.reference].flatMap((ref) => (ref ? [ref.secret_ref] : []));
}

function mapProfile(working: WorkingCopy, profileId: string, change: (profile: BusinessDocument["payments"][number]) => BusinessDocument["payments"][number]): BusinessDocument {
  return { ...working.document, payments: working.document.payments.map((profile) => (profile.id === profileId ? change(profile) : profile)) };
}

/** Crea un perfil de pago y lo asigna a lo que aún no tiene uno. */
export function addPaymentProfile({ document, paymentValues }: WorkingCopy): WorkingCopy {
  const taken = new Set(document.payments.map((profile) => profile.id));
  let id = "principal";
  for (let number = 2; taken.has(id); number += 1) id = `perfil_${number}`;
  const next: BusinessDocument = {
    ...document,
    payments: [...document.payments, { id, link: null, transfer_enabled: false, transfer_methods: [] }],
    offer: {
      ...document.offer,
      plans: document.offer.plans?.map((plan) => ({ ...plan, payment_profile: plan.payment_profile ?? id })) ?? document.offer.plans ?? null,
      catalog: document.offer.catalog ? { ...document.offer.catalog, payment_profile: document.offer.catalog.payment_profile ?? id } : (document.offer.catalog ?? null),
    },
  };
  return { document: next, paymentValues };
}

/** Quita el perfil; lo que lo usaba queda sin perfil asignado. */
export function removePaymentProfile(working: WorkingCopy, profileId: string): WorkingCopy {
  const { document, paymentValues } = working;
  const profile = document.payments.find((item) => item.id === profileId);
  const refs = profile ? paymentHolders([profile]).map((holder) => holder.ref.secret_ref) : [];
  return {
    document: {
      ...document,
      payments: document.payments.filter((item) => item.id !== profileId),
      offer: {
        ...document.offer,
        plans: document.offer.plans?.map((plan) => (plan.payment_profile === profileId ? { ...plan, payment_profile: null } : plan)) ?? document.offer.plans ?? null,
        catalog: document.offer.catalog?.payment_profile === profileId ? { ...document.offer.catalog, payment_profile: null } : (document.offer.catalog ?? null),
      },
    },
    paymentValues: withoutValues(paymentValues, refs),
  };
}

/** Quita el enlace de esta versión. Las versiones anteriores conservan el suyo. */
export function removePaymentLink(working: WorkingCopy, profileId: string): WorkingCopy {
  const current = working.document.payments.find((profile) => profile.id === profileId)?.link;
  return {
    document: mapProfile(working, profileId, (profile) => ({ ...profile, link: null, link_enabled: null })),
    paymentValues: current ? withoutValues(working.paymentValues, [current.secret_ref]) : working.paymentValues,
  };
}

/**
 * Activa o desactiva el enlace. Uno ya guardado se conserva al desactivarlo, para poder activarlo sin escribirlo de nuevo;
 * uno que aún no se ha guardado se descarta. Activar sin enlace pide un valor nuevo.
 */
export function setPaymentLinkEnabled(working: WorkingCopy, profileId: string, enabled: boolean): WorkingCopy {
  const profile = working.document.payments.find((item) => item.id === profileId);
  const current = profile?.link;
  if (!enabled) {
    if (!current || !isStoredRef(current.secret_ref)) return removePaymentLink(working, profileId);
    return { ...working, document: mapProfile(working, profileId, (item) => ({ ...item, link_enabled: false })) };
  }
  if (current) return profile?.link_enabled === false ? { ...working, document: mapProfile(working, profileId, (item) => ({ ...item, link_enabled: null })) } : working;
  const ref = newSecretRef(profileId, "link");
  return { document: mapProfile(working, profileId, (item) => ({ ...item, link: { secret_ref: ref } })), paymentValues: { ...working.paymentValues, [ref]: "" } };
}

export function setPaymentValue(working: WorkingCopy, ref: string, value: string): WorkingCopy {
  return { ...working, paymentValues: { ...working.paymentValues, [ref]: value } };
}

/** Deja de reemplazar un dato ya guardado: se conserva el que había. */
export function keepStoredPaymentValue(working: WorkingCopy, ref: string): WorkingCopy {
  return { ...working, paymentValues: withoutValues(working.paymentValues, [ref]) };
}

/** Al desactivar transferencias se conservan las cuentas guardadas; las nuevas que aún no tienen dato se descartan. */
export function setTransferEnabled(working: WorkingCopy, profileId: string, enabled: boolean): WorkingCopy {
  const profile = working.document.payments.find((item) => item.id === profileId);
  const methods = profile?.transfer_methods ?? [];
  const incomplete = (method: TransferMethod) => refsOfMethod(method).some((ref) => !isStoredRef(ref) && working.paymentValues[ref] !== undefined && !working.paymentValues[ref]?.trim());
  const dropped = enabled ? [] : methods.filter(incomplete);
  return {
    document: mapProfile(working, profileId, (item) => ({ ...item, transfer_enabled: enabled, transfer_methods: methods.filter((method) => !dropped.includes(method)) })),
    paymentValues: withoutValues(working.paymentValues, dropped.flatMap(refsOfMethod)),
  };
}

function newTransferMethod(profileId: string, type: TransferMethodType): { method: TransferMethod; ref: string } {
  switch (type) {
    case "nequi":
    case "daviplata": {
      const ref = newSecretRef(profileId, `${type}.number`);
      return { method: { type, number: { secret_ref: ref } }, ref };
    }
    case "bank": {
      const ref = newSecretRef(profileId, "bank.account_number");
      return { method: { type, bank: "", account_type: "ahorros", account_number: { secret_ref: ref } }, ref };
    }
    case "breb": {
      const ref = newSecretRef(profileId, "breb.reference");
      return { method: { type, reference: { secret_ref: ref } }, ref };
    }
  }
}

export function addTransferMethod(working: WorkingCopy, profileId: string): WorkingCopy {
  const { method, ref } = newTransferMethod(profileId, "nequi");
  return {
    document: mapProfile(working, profileId, (profile) => ({ ...profile, transfer_methods: [...(profile.transfer_methods ?? []), method] })),
    paymentValues: { ...working.paymentValues, [ref]: "" },
  };
}

export function removeTransferMethod(working: WorkingCopy, profileId: string, index: number): WorkingCopy {
  const methods = working.document.payments.find((profile) => profile.id === profileId)?.transfer_methods ?? [];
  const removed = methods[index];
  return {
    document: mapProfile(working, profileId, (profile) => ({ ...profile, transfer_methods: methods.filter((_, position) => position !== index) })),
    paymentValues: removed ? withoutValues(working.paymentValues, refsOfMethod(removed)) : working.paymentValues,
  };
}

/** Datos que no son sensibles de una cuenta (banco, tipo de cuenta y titular o etiqueta). El dato cifrado no se toca. */
export function updateTransferMethod(working: WorkingCopy, profileId: string, index: number, patch: Pick<TransferMethod, "bank" | "account_type" | "label">): WorkingCopy {
  return updateMethod(working, profileId, index, patch);
}

/** Una cuenta inactiva conserva sus datos, pero no se ofrece. Activa es lo normal, así que no se indica. */
export function setTransferMethodEnabled(working: WorkingCopy, profileId: string, index: number, enabled: boolean): WorkingCopy {
  return updateMethod(working, profileId, index, { enabled: enabled ? null : false });
}

function updateMethod(working: WorkingCopy, profileId: string, index: number, patch: Partial<TransferMethod>): WorkingCopy {
  return {
    ...working,
    document: mapProfile(working, profileId, (profile) => ({
      ...profile,
      transfer_methods: (profile.transfer_methods ?? []).map((method, position) => (position === index ? { ...method, ...patch } : method)),
    })),
  };
}

/** Cambia el tipo de una cuenta: los datos del tipo anterior se descartan, salvo su etiqueta y su estado. Cambiar al mismo tipo no modifica nada. */
export function changeTransferMethodType(working: WorkingCopy, profileId: string, index: number, type: TransferMethodType): WorkingCopy {
  const methods = working.document.payments.find((profile) => profile.id === profileId)?.transfer_methods ?? [];
  const current = methods[index];
  if (!current || current.type === type) return working;
  const created = newTransferMethod(profileId, type);
  const { ref } = created;
  const method: TransferMethod = { ...created.method, label: current.label ?? null, enabled: current.enabled ?? null };
  return {
    document: mapProfile(working, profileId, (profile) => ({ ...profile, transfer_methods: methods.map((item, position) => (position === index ? method : item)) })),
    paymentValues: { ...withoutValues(working.paymentValues, refsOfMethod(current)), [ref]: "" },
  };
}
