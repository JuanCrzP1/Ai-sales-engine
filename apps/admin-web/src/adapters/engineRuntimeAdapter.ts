import { isPrimaryAction } from "../domain/config/options";
import type { AssistantConfig, Offering, PaymentSettings, ResponseLength, TransferMethod } from "../domain/config/types";
import { cleanList } from "../lib/text";
import type {
  EngineCatalog,
  EnginePaymentBlock,
  EnginePlan,
  EngineTenantSections,
  EngineTransferMethod,
} from "./engineTypes";

/**
 * Traduce la configuración del panel a las cinco secciones que leen hoy los YAML del motor.
 *
 * CONTRATO PROVISIONAL, NO APROBADO: refleja el formato actual de los YAML y se revisará
 * cuando se corrijan. Función pura, sin E/S: no escribe YAML ni llama a ningún servicio.
 * No valida ni avisa: para eso existe `translateToEngine` (validación, contrato y avisos).
 *
 * Decisiones (documentadas en README):
 * - Los elementos marcados como no disponibles no se envían al motor.
 * - El bloque de pago se repite en cada plan (o en el catálogo), igual que en los
 *   negocios existentes, porque el motor lo lee en esas ubicaciones.
 * - Las ventanas de conversación se omiten para que el motor use sus valores por defecto.
 */

export const MAX_WORDS_BY_LENGTH: Record<ResponseLength, number> = {
  short: 60,
  medium: 75,
  long: 100,
};

export function toEngineSections(config: AssistantConfig): EngineTenantSections {
  const { business, behavior, closing, messages } = config;
  const isCatalog = business.salesMode === "catalog";
  const offerings = config.offerings.filter((offering) => offering.available);
  const paymentBlock = toPaymentBlock(config.payments);
  const motivations = { primary: behavior.primaryMotivation.trim(), secondary: behavior.secondaryMotivation.trim() };

  return {
    business: {
      name: business.name.trim(),
      brand_name: business.name.trim(),
      industry: business.businessType.trim(),
      description: business.description.trim(),
      promise: business.valueProposition.trim(),
      tone: behavior.tone,
      ...(motivations.primary || motivations.secondary ? { buying_motivation: motivations } : {}),
    },
    sales: {
      pain: {
        clusters: Object.fromEntries(
          cleanList(behavior.customerProblems).map((problem, index) => [`problema_${index + 1}`, { impacts: [problem] }]),
        ),
      },
      discovery: { questions: cleanList(behavior.discoveryQuestions) },
      closing: { hard_rules: cleanList(behavior.salesRules) },
      offer: {
        recommendation_rules: behavior.recommendationNotes.trim()
          ? [{ condition: "general", recommend: behavior.recommendationNotes.trim() }]
          : [],
      },
    },
    pricing: {
      ...(isCatalog
        ? { model: "catalog" as const, catalog: toCatalog(offerings, paymentBlock) }
        : { plans: offerings.map((offering) => toPlan(offering, paymentBlock)) }),
      conditions: cleanList(config.payments.conditions),
    },
    inventory: { track_stock: false, items: [] },
    config: {
      initial_message: { enabled: messages.welcomeEnabled, text: messages.welcomeText.trim() },
      features: {
        pricing_enabled: true,
        catalog_mode: isCatalog,
        ...(isCatalog ? { business_model: "catalog" as const } : {}),
      },
      response: { length: behavior.responseLength, max_words: MAX_WORDS_BY_LENGTH[behavior.responseLength] },
      post_payment: {
        on_user_report: { message: messages.paymentReportedText.trim() },
        on_payment_confirmed: { message: messages.paymentConfirmedText.trim() },
      },
      capabilities: {
        channels: [...messages.serviceChannels],
        business_channels: { allowed: [...messages.serviceChannels] },
        system_channels: { allowed: [] },
        actions: {
          primary: closing.actions.filter(isPrimaryAction),
          support: closing.actions.filter((action) => !isPrimaryAction(action)),
        },
        closing_methods: {
          link_payment: { enabled: closing.sendPaymentLink },
          human_handoff: { enabled: closing.humanHandoff },
          data_collection: { enabled: closing.collectCustomerData },
        },
        data_collection: {
          enabled: closing.collectCustomerData,
          fields: closing.collectCustomerData ? [...closing.customerDataFields] : [],
        },
      },
    },
  };
}

function toPaymentBlock(payments: PaymentSettings): EnginePaymentBlock {
  return {
    link: payments.paymentLinkEnabled ? payments.paymentLink.trim() : "",
    transfer: {
      enabled: payments.transferEnabled && payments.transferMethods.length > 0,
      methods: payments.transferEnabled ? payments.transferMethods.map(toTransferMethod) : [],
    },
  };
}

function toTransferMethod(method: TransferMethod): EngineTransferMethod {
  switch (method.type) {
    case "nequi":
    case "daviplata":
      return { type: method.type, number: method.phoneNumber.replace(/\s+/g, "") };
    case "bank":
      return {
        type: "bank",
        bank: method.bankName.trim(),
        account_type: method.accountType,
        account_number: method.accountNumber.replace(/[\s-]+/g, ""),
      };
    case "breb":
      return { type: "breb", reference: method.reference.trim() };
  }
}

function toPlan(offering: Offering, payment: EnginePaymentBlock): EnginePlan {
  const values: EnginePlan["pricing"][string] = {};
  if (offering.setupFee !== null) values.implementation = offering.setupFee;
  if (offering.price !== null) values[offering.billing === "monthly" ? "monthly" : "price"] = offering.price;
  return {
    id: offering.id,
    name: offering.name.trim(),
    description: offering.description.trim(),
    pricing: { [offering.currency]: values },
    includes: cleanList(offering.features),
    not_included: cleanList(offering.notIncluded),
    payment,
  };
}

export function categoryId(name: string): string {
  return (
    name
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "") || "general"
  );
}

function toCatalog(offerings: Offering[], payment: EnginePaymentBlock): EngineCatalog {
  // Categorías que se escriben igual sin tildes ni mayúsculas comparten id: se conserva el primer nombre.
  const categories = new Map<string, string>();
  for (const offering of offerings) {
    const name = offering.category.trim() || "General";
    const id = categoryId(name);
    if (!categories.has(id)) categories.set(id, name);
  }
  return {
    categories: [...categories].map(([id, name]) => ({ id, name })),
    items: offerings.map((offering) => ({
      id: offering.id,
      name: offering.name.trim(),
      category: categoryId(offering.category.trim() || "General"),
      description: offering.description.trim(),
      price: offering.price !== null ? { [offering.currency]: offering.price } : {},
    })),
    payment,
  };
}
