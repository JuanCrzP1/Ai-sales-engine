import { engineUsage, MAX_CATEGORIES_USED, MAX_PROBLEMS_USED, type ConfigField } from "../domain/config/engineUsage";
import { isKnownAction } from "../domain/config/options";
import type { AssistantConfig } from "../domain/config/types";
import { cleanList } from "../lib/text";
import { categoryId } from "./engineRuntimeAdapter";

/**
 * Avisos de la traducción al motor: datos que no se envían, que se fusionan o que el
 * motor actual recibe pero no usa. Así nada se pierde en silencio.
 */
export type EngineNoticeCode =
  | "offering_unavailable_omitted"
  | "catalog_field_dropped"
  | "plan_category_dropped"
  | "category_defaulted"
  | "categories_merged"
  | "categories_beyond_limit"
  | "price_missing"
  | "payment_link_disabled_dropped"
  | "transfer_methods_disabled_dropped"
  | "transfer_type_duplicated"
  | "problems_beyond_limit"
  | "unknown_action"
  | "human_handoff_not_notified"
  | "field_not_consumed";

export interface EngineNotice {
  code: EngineNoticeCode;
  message: string;
  /** Campo o elemento del panel al que se refiere, cuando aplica. */
  field?: string;
}

export function collectEngineNotices(config: AssistantConfig): EngineNotice[] {
  return [...offeringNotices(config), ...paymentNotices(config), ...behaviorNotices(config), ...unusedFieldNotices(config)];
}

function offeringNotices(config: AssistantConfig): EngineNotice[] {
  const notices: EngineNotice[] = [];
  const isCatalog = config.business.salesMode === "catalog";
  const available = config.offerings.filter((offering) => offering.available);

  for (const offering of config.offerings) {
    const label = offering.name.trim() || offering.id;
    const field = `offerings.${offering.id}`;
    if (!offering.available) {
      notices.push({ code: "offering_unavailable_omitted", field, message: `"${label}" no está disponible y no se envía.` });
      continue;
    }
    if (offering.price === null) notices.push({ code: "price_missing", field, message: `"${label}" no tiene precio: se envía sin valor.` });
    if (isCatalog) {
      const dropped = [
        cleanList(offering.features).length > 0 ? "características" : "",
        cleanList(offering.notIncluded).length > 0 ? "lo que no incluye" : "",
        offering.setupFee !== null ? "costo inicial" : "",
        offering.billing === "monthly" ? "cobro mensual" : "",
      ].filter(Boolean);
      if (dropped.length > 0) {
        notices.push({ code: "catalog_field_dropped", field, message: `En catálogo no se envía de "${label}": ${dropped.join(", ")}.` });
      }
      if (!offering.category.trim()) {
        notices.push({ code: "category_defaulted", field, message: `"${label}" no tiene categoría: se agrupa en "General".` });
      }
    } else if (offering.category.trim()) {
      notices.push({ code: "plan_category_dropped", field, message: `En planes no se envía la categoría de "${label}".` });
    }
  }

  if (isCatalog) {
    const namesById = new Map<string, Set<string>>();
    for (const offering of available) {
      const name = offering.category.trim() || "General";
      const id = categoryId(name);
      namesById.set(id, (namesById.get(id) ?? new Set()).add(name));
    }
    for (const [id, names] of namesById) {
      if (names.size > 1) {
        const [kept, ...merged] = [...names];
        notices.push({
          code: "categories_merged",
          field: `category.${id}`,
          message: `Las categorías ${[...names].map((name) => `"${name}"`).join(", ")} se unen en una sola ("${kept}"); ${merged.length === 1 ? "la otra se escribe" : "las otras se escriben"} igual sin tildes ni mayúsculas.`,
        });
      }
    }
    if (namesById.size > MAX_CATEGORIES_USED) {
      notices.push({
        code: "categories_beyond_limit",
        message: `Hay ${namesById.size} categorías; el motor actual solo menciona las primeras ${MAX_CATEGORIES_USED}.`,
      });
    }
  }
  return notices;
}

function paymentNotices({ payments, closing }: AssistantConfig): EngineNotice[] {
  const notices: EngineNotice[] = [];
  if (!payments.paymentLinkEnabled && payments.paymentLink.trim()) {
    notices.push({ code: "payment_link_disabled_dropped", field: "payments.paymentLink", message: "El enlace de pago está desactivado y no se envía." });
  }
  if (!payments.transferEnabled && payments.transferMethods.length > 0) {
    notices.push({
      code: "transfer_methods_disabled_dropped",
      field: "payments.transferMethods",
      message: "Las transferencias están desactivadas: sus cuentas no se envían.",
    });
  }
  if (payments.transferEnabled) {
    const seen = new Set<string>();
    for (const method of payments.transferMethods) {
      if (seen.has(method.type)) {
        notices.push({
          code: "transfer_type_duplicated",
          field: `payments.transfer.${method.id}`,
          message: `Hay más de una cuenta de tipo "${method.type}": el motor actual solo usa la primera.`,
        });
      }
      seen.add(method.type);
    }
  }
  for (const action of closing.actions) {
    if (!isKnownAction(action)) {
      notices.push({ code: "unknown_action", field: "closing.actions", message: `La acción "${action}" no es conocida: se envía como acción de apoyo.` });
    }
  }
  if (closing.humanHandoff) {
    notices.push({
      code: "human_handoff_not_notified",
      field: "closing.humanHandoff",
      message: "Se envía la atención por una persona, pero el motor actual no avisa a nadie del equipo.",
    });
  }
  return notices;
}

function behaviorNotices({ behavior }: AssistantConfig): EngineNotice[] {
  const problems = cleanList(behavior.customerProblems);
  return problems.length > MAX_PROBLEMS_USED
    ? [
        {
          code: "problems_beyond_limit",
          field: "behavior.customerProblems",
          message: `Hay ${problems.length} problemas; el motor actual solo usa los ${MAX_PROBLEMS_USED} primeros.`,
        },
      ]
    : [];
}

/** Datos que se envían pero que el motor actual no usa al responder (según `engineUsage`). */
function unusedFieldNotices(config: AssistantConfig): EngineNotice[] {
  const { business, behavior, offerings } = config;
  const available = offerings.filter((offering) => offering.available);
  const filled: [ConfigField, boolean][] = [
    ["business.name", Boolean(business.name.trim())],
    ["business.description", Boolean(business.description.trim())],
    ["behavior.tone", true],
    ["behavior.salesRules", cleanList(behavior.salesRules).length > 0],
    ["behavior.discoveryQuestions", cleanList(behavior.discoveryQuestions).length > 0],
    ["behavior.recommendationNotes", Boolean(behavior.recommendationNotes.trim())],
    ["offering.name", available.length > 0],
    ["offering.description", available.some((offering) => offering.description.trim())],
    ["offering.price", available.some((offering) => offering.price !== null)],
    ["offering.features", available.some((offering) => cleanList(offering.features).length > 0)],
  ];
  return filled
    .filter(([field, hasValue]) => hasValue && engineUsage(field, business.salesMode) === "stored")
    .map(([field]) => ({ code: "field_not_consumed" as const, field, message: `"${field}" se envía, pero el motor actual no lo usa al responder.` }));
}
