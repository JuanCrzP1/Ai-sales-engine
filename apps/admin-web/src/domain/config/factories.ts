import { createId } from "../../lib/ids";
import type { AssistantConfig, FaqEntry, Offering, Promotion, RecommendationRule, TransferMethod } from "./types";

export function createFaq(overrides: Partial<FaqEntry> = {}): FaqEntry {
  return { id: createId("pregunta"), question: "", answer: "", ...overrides };
}

export function createRecommendationRule(overrides: Partial<RecommendationRule> = {}): RecommendationRule {
  return { id: createId("recomendacion"), when: "", offeringId: "", ...overrides };
}

export function createPromotion(overrides: Partial<Promotion> = {}): Promotion {
  return { id: createId("promocion"), name: "", details: "", validUntil: "", ...overrides };
}

/**
 * Completa una configuración guardada con los campos que se añadieron después (p. ej. `faqs`,
 * la ubicación o las promociones), sin descartar lo que ya tenía.
 */
export function withDefaults(config: AssistantConfig): AssistantConfig {
  const empty = createEmptyConfig();
  return {
    ...config,
    business: {
      ...empty.business,
      ...config.business,
      location: { ...empty.business.location, ...config.business.location },
    },
    payments: { ...empty.payments, ...config.payments },
    behavior: { ...empty.behavior, ...config.behavior },
  };
}

export function createOffering(overrides: Partial<Offering> = {}): Offering {
  return {
    id: createId("oferta"),
    name: "",
    description: "",
    category: "",
    price: null,
    setupFee: null,
    currency: "COP",
    billing: "one_time",
    features: [],
    notIncluded: [],
    available: true,
    ...overrides,
  };
}

export function createTransferMethod(overrides: Partial<TransferMethod> = {}): TransferMethod {
  return {
    id: createId("transferencia"),
    type: "nequi",
    phoneNumber: "",
    bankName: "",
    accountType: "ahorros",
    accountNumber: "",
    reference: "",
    ...overrides,
  };
}

/** Configuración vacía: punto de partida para un negocio nuevo. */
export function createEmptyConfig(): AssistantConfig {
  return {
    version: 1,
    business: {
      name: "",
      brandName: "",
      businessType: "",
      description: "",
      valueProposition: "",
      salesMode: "plans",
      differentiators: [],
      location: { type: "", address: "", city: "", coverageType: "local", coverageZones: [] },
      serviceModes: [],
    },
    offerings: [],
    payments: {
      paymentLinkEnabled: false,
      paymentLink: "",
      transferEnabled: false,
      transferMethods: [],
      conditions: [],
      promotions: [],
    },
    closing: {
      sendPaymentLink: false,
      humanHandoff: false,
      collectCustomerData: true,
      customerDataFields: ["nombre", "telefono"],
      actions: ["responder_dudas"],
    },
    behavior: {
      tone: "",
      responseLength: "short",
      maxWords: null,
      primaryMotivation: "",
      secondaryMotivation: "",
      customerProblems: [],
      benefits: [],
      sellingPoints: [],
      discoveryQuestions: [],
      recommendationRules: [],
      salesInstructions: [],
      faqs: [],
    },
    messages: {
      welcomeEnabled: false,
      welcomeText: "",
      paymentReportedText: "",
      paymentConfirmedText: "",
      serviceChannels: ["whatsapp"],
    },
  };
}
