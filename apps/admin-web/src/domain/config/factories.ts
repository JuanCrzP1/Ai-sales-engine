import { createId } from "../../lib/ids";
import type { AssistantConfig, Offering, TransferMethod } from "./types";

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
      businessType: "",
      description: "",
      valueProposition: "",
      salesMode: "plans",
    },
    offerings: [],
    payments: {
      paymentLinkEnabled: false,
      paymentLink: "",
      transferEnabled: false,
      transferMethods: [],
      conditions: [],
    },
    closing: {
      sendPaymentLink: false,
      humanHandoff: false,
      collectCustomerData: true,
      customerDataFields: ["nombre", "telefono"],
      actions: ["responder_dudas"],
    },
    behavior: {
      tone: "cercano",
      responseLength: "short",
      primaryMotivation: "",
      secondaryMotivation: "",
      customerProblems: [],
      salesRules: [],
      discoveryQuestions: [],
      recommendationNotes: "",
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
