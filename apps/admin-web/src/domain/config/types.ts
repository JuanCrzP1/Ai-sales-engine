/**
 * Modelo de configuración del asistente tal como lo entiende el cliente.
 *
 * Es independiente del formato interno del motor (los cinco YAML por negocio).
 * La traducción a ese formato vive en `adapters/engineRuntimeAdapter.ts`.
 */

export type SalesMode = "plans" | "catalog";

export type Currency = "COP" | "USD";

/** Cómo se cobra un plan o servicio. Un producto de catálogo siempre es pago único. */
export type BillingType = "one_time" | "monthly";

export type ResponseLength = "short" | "medium" | "long";

export type CommunicationTone = "cercano" | "profesional" | "formal" | "entusiasta";

export type TransferMethodType = "nequi" | "daviplata" | "bank" | "breb";

export type BankAccountType = "ahorros" | "corriente";

export interface BusinessProfile {
  /** Nombre comercial que verá el cliente final. */
  name: string;
  /** A qué se dedica el negocio, en pocas palabras. */
  businessType: string;
  /** Descripción libre del negocio. */
  description: string;
  /** Propuesta de valor o promesa comercial. */
  valueProposition: string;
  /** Si vende planes/servicios o un catálogo de productos. */
  salesMode: SalesMode;
}

export interface Offering {
  id: string;
  name: string;
  description: string;
  /** Agrupa productos en el modo catálogo (por ejemplo, "Bebidas"). */
  category: string;
  price: number | null;
  /** Costo inicial opcional para planes o servicios (instalación, implementación). */
  setupFee: number | null;
  currency: Currency;
  billing: BillingType;
  /** Lo que incluye o sus características relevantes. */
  features: string[];
  /** Lo que no incluye (solo planes o servicios). */
  notIncluded: string[];
  available: boolean;
}

export interface TransferMethod {
  id: string;
  type: TransferMethodType;
  /** Número de celular para Nequi o Daviplata. */
  phoneNumber: string;
  bankName: string;
  accountType: BankAccountType;
  accountNumber: string;
  /** Llave o referencia Bre-B. */
  reference: string;
}

export interface PaymentSettings {
  paymentLinkEnabled: boolean;
  paymentLink: string;
  transferEnabled: boolean;
  transferMethods: TransferMethod[];
  conditions: string[];
}

export interface ClosingSettings {
  sendPaymentLink: boolean;
  humanHandoff: boolean;
  collectCustomerData: boolean;
  customerDataFields: string[];
  /** Acciones que el asistente puede realizar (claves de `ASSISTANT_ACTIONS`). */
  actions: string[];
}

export interface AssistantBehavior {
  tone: CommunicationTone;
  responseLength: ResponseLength;
  /** Principal razón por la que compran (por ejemplo, ahorrar tiempo). */
  primaryMotivation: string;
  secondaryMotivation: string;
  /** Problemas de los clientes que el negocio resuelve. */
  customerProblems: string[];
  salesRules: string[];
  discoveryQuestions: string[];
  recommendationNotes: string;
}

export interface MessageSettings {
  welcomeEnabled: boolean;
  welcomeText: string;
  paymentReportedText: string;
  paymentConfirmedText: string;
  /** Canales que el asistente puede mencionar como medios de atención. */
  serviceChannels: string[];
}

export interface AssistantConfig {
  version: 1;
  business: BusinessProfile;
  offerings: Offering[];
  payments: PaymentSettings;
  closing: ClosingSettings;
  behavior: AssistantBehavior;
  messages: MessageSettings;
}
