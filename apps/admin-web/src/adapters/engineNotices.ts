import { MAX_CATEGORIES_USED, MAX_PROBLEMS_USED } from "../domain/config/engineLimits";
import { isKnownAction } from "../domain/config/options";
import type { AssistantConfig } from "../domain/config/types";
import { localIsoDate } from "../lib/format";
import { cleanList } from "../lib/text";
import { categoryId } from "./contractAdapter";

/**
 * Avisos de la traducción al motor: datos que no se envían, que se fusionan o que el motor
 * usa de forma limitada. Así nada se pierde en silencio.
 */
export type EngineNoticeCode =
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
  | "recommendation_omitted"
  | "promotion_omitted"
  | "promotion_expired";

export interface EngineNotice {
  code: EngineNoticeCode;
  message: string;
  /** Campo o elemento del panel al que se refiere, cuando aplica. */
  field?: string;
}

export function collectEngineNotices(config: AssistantConfig): EngineNotice[] {
  return [...offeringNotices(config), ...paymentNotices(config), ...behaviorNotices(config)];
}

function offeringNotices(config: AssistantConfig): EngineNotice[] {
  const notices: EngineNotice[] = [];
  const isCatalog = config.business.salesMode === "catalog";

  for (const offering of config.offerings) {
    const label = offering.name.trim() || offering.id;
    const field = `offerings.${offering.id}`;
    if (offering.price === null) notices.push({ code: "price_missing", field, message: `"${label}" no tiene precio: se envía sin valor.` });
    if (isCatalog) {
      const dropped = [
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
    for (const offering of config.offerings) {
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

function behaviorNotices({ behavior, offerings, payments }: AssistantConfig, today = new Date()): EngineNotice[] {
  const notices: EngineNotice[] = [];
  const problems = cleanList(behavior.customerProblems);
  if (problems.length > MAX_PROBLEMS_USED) {
    notices.push({
      code: "problems_beyond_limit",
      field: "behavior.customerProblems",
      message: `Hay ${problems.length} problemas; el motor actual solo usa los ${MAX_PROBLEMS_USED} primeros.`,
    });
  }
  const offeringIds = new Set(offerings.map((offering) => offering.id));
  for (const rule of behavior.recommendationRules) {
    if (!rule.when.trim() || !offeringIds.has(rule.offeringId)) {
      notices.push({
        code: "recommendation_omitted",
        field: `behavior.recommendationRules.${rule.id}`,
        message: "Una recomendación sin situación o sin un plan o producto de la oferta no se envía.",
      });
    }
  }
  const todayIso = localIsoDate(today);
  for (const promotion of payments.promotions) {
    const field = `payments.promotions.${promotion.id}`;
    if (!promotion.name.trim() || !promotion.details.trim()) {
      notices.push({ code: "promotion_omitted", field, message: "Una promoción sin nombre o sin detalle no se envía." });
    } else if (promotion.validUntil && promotion.validUntil < todayIso) {
      notices.push({ code: "promotion_expired", field, message: `"${promotion.name.trim()}" ya venció: el asistente no la ofrecerá.` });
    }
  }
  return notices;
}
