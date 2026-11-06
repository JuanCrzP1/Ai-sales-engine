import type { CatalogItem, Plan, PlanPrice } from "../../contracts/businessConfig.v1";
import { SCHEMA_VERSION } from "../../contracts/businessConfig.v1";
import { createId } from "../../lib/ids";
import type { BusinessDocument } from "./types";

export const DEFAULT_CURRENCY = "COP";
const SECRET_SOURCE = "secret_store";

/** Id legible a partir de un nombre: minúsculas, sin tildes y con guion bajo. */
export function toIdentifier(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

export function categoryId(name: string): string {
  return toIdentifier(name) || "general";
}

/** Referencia para un dato de pago nuevo; el servidor la versiona al guardarlo. */
export function newSecretRef(profileId: string, field: string): string {
  return `${SECRET_SOURCE}:${profileId}.${field}.${createId("dato")}`;
}

export function createPlan(overrides: Partial<Plan> = {}): Plan {
  return { id: createId("plan"), name: "", prices: [{ currency: DEFAULT_CURRENCY }], includes: [], not_included: [], available: true, ...overrides };
}

export function createCatalogItem(overrides: Partial<CatalogItem> = {}): CatalogItem {
  return { id: createId("producto"), name: "", category: "", prices: [{ currency: DEFAULT_CURRENCY, amount: 0 }], available: true, ...overrides };
}

/** Importe principal de un precio de plan, para mostrarlo en listas. */
export function mainPlanAmount(price: PlanPrice): { amount: number | null; period: "mes" | "año" | null } {
  if (price.monthly != null) return { amount: price.monthly, period: "mes" };
  if (price.price != null) return { amount: price.price, period: null };
  if (price.annual != null) return { amount: price.annual, period: "año" };
  return { amount: price.implementation ?? price.first_payment ?? null, period: null };
}

/**
 * Punto de partida de un negocio nuevo. Todavía no cumple el contrato (falta lo que solo el negocio puede decir):
 * se guarda por primera vez cuando el servidor lo acepta.
 */
export function createEmptyDocument(slug: string, name: string): BusinessDocument {
  return {
    schema_version: SCHEMA_VERSION as BusinessDocument["schema_version"],
    tenant_slug: slug,
    identity: { name, industry: "", description: "", value_proposition: "" },
    offer: { model: "plans", plans: [] },
    terms: {},
    payments: [],
    sales: {},
    capabilities: {
      service_channels: ["whatsapp"],
      product_channels: [],
      actions_primary: [],
      actions_support: ["responder_dudas"],
      closing_methods: { payment_link: false, human_handoff: false, data_collection: true },
      data_collection: { enabled: true, fields: ["nombre", "telefono"] },
    },
    messages: { welcome: { enabled: false, text: "" } },
    response_style: { length: "short" },
    knowledge: { faqs: [] },
    inventory: { items: [] },
  };
}
