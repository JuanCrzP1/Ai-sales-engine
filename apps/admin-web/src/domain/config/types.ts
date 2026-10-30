/**
 * Modelo de configuración del asistente tal como lo entiende el cliente.
 *
 * Es independiente del contrato del motor (BusinessConfig v1).
 * La traducción al contrato global del motor vive en `adapters/contractAdapter.ts`.
 */

export type SalesMode = "plans" | "catalog";

export type Currency = "COP" | "USD";

/** Cómo se cobra un plan o servicio. Un producto de catálogo siempre es pago único. */
export type BillingType = "one_time" | "monthly";

export type ResponseLength = "short" | "medium" | "long";

export type TransferMethodType = "nequi" | "daviplata" | "bank" | "breb";

export type BankAccountType = "ahorros" | "corriente";

/** Dónde atiende el negocio; "" significa que no lo indica. */
export type LocationType = "" | "virtual" | "fisico" | "mixto";

export type CoverageType = "local" | "nacional" | "internacional";

export type ServiceMode = "virtual" | "presencial" | "domicilio" | "recoger" | "envio";

export interface BusinessLocation {
  type: LocationType;
  /** Dirección del local (si tiene local físico). */
  address: string;
  city: string;
  coverageType: CoverageType;
  /** Barrios, ciudades o países a los que atiende o envía. */
  coverageZones: string[];
}

export interface BusinessProfile {
  /** Nombre comercial que verá el cliente final. */
  name: string;
  /** Marca con la que el asistente presenta al negocio, si es distinta del nombre. */
  brandName: string;
  /** A qué se dedica el negocio, en pocas palabras. */
  businessType: string;
  /** Descripción libre del negocio. */
  description: string;
  /** Propuesta de valor o promesa comercial. */
  valueProposition: string;
  /** Si vende planes/servicios o un catálogo de productos. */
  salesMode: SalesMode;
  /** Por qué elegir este negocio y no otro. */
  differentiators: string[];
  location: BusinessLocation;
  serviceModes: ServiceMode[];
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
  /** Únicas promociones o descuentos que el asistente puede ofrecer. */
  promotions: Promotion[];
}

export interface Promotion {
  id: string;
  name: string;
  details: string;
  /** Último día de vigencia (AAAA-MM-DD) o vacío si no vence. */
  validUntil: string;
}

export interface ClosingSettings {
  sendPaymentLink: boolean;
  humanHandoff: boolean;
  collectCustomerData: boolean;
  customerDataFields: string[];
  /** Acciones que el asistente puede realizar (claves de `ASSISTANT_ACTIONS`). */
  actions: string[];
}

/** Qué debe recomendar el asistente en una situación concreta del cliente. */
export interface RecommendationRule {
  id: string;
  when: string;
  /** Id del plan, servicio o producto recomendado. */
  offeringId: string;
}

/** Pregunta frecuente que el asistente puede consultar para responder. */
export interface FaqEntry {
  id: string;
  question: string;
  answer: string;
}

export interface AssistantBehavior {
  /** Cómo habla el asistente (por ejemplo, cercano y claro). */
  tone: string;
  /** Largo de las respuestas: fija el límite de palabras del motor. */
  responseLength: ResponseLength;
  /** Ajuste avanzado dentro del rango de `responseLength`; null usa el límite de la opción. */
  maxWords: number | null;
  /** Principal razón por la que compran (por ejemplo, ahorrar tiempo). */
  primaryMotivation: string;
  secondaryMotivation: string;
  /** Problemas de los clientes que el negocio resuelve. */
  customerProblems: string[];
  /** Resultados que obtiene el cliente. */
  benefits: string[];
  /** Argumentos de venta. */
  sellingPoints: string[];
  /** Preguntas para entender al cliente antes de recomendar. */
  discoveryQuestions: string[];
  recommendationRules: RecommendationRule[];
  /** Instrucciones de venta propias del negocio. */
  salesInstructions: string[];
  /** Conocimiento del negocio: preguntas frecuentes y sus respuestas. */
  faqs: FaqEntry[];
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
