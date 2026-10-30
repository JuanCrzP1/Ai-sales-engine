import type {
  BusinessConfig,
  CatalogItem,
  Location,
  PaymentProfile,
  Plan,
  PlanPrice,
  RecommendationRule,
  SecretRef,
  TransferMethod as ContractTransferMethod,
} from "../contracts/businessConfig.v1";
import { SCHEMA_VERSION } from "../contracts/businessConfig.v1";
import { isPrimaryAction } from "../domain/config/options";
import type { AssistantConfig, BusinessLocation, Offering, TransferMethod } from "../domain/config/types";
import { cleanList } from "../lib/text";

/**
 * Traduce la configuración del panel al contrato global (BusinessConfig v1).
 *
 * Función pura, sin E/S. Los datos de pago sensibles (link, celulares, cuentas, llaves) no se
 * incluyen en el documento: se devuelven aparte en `secrets`, indexados por la misma referencia
 * `secret_store:<clave>` que usa el documento, para guardarlos en el almacén de secretos.
 *
 * Decisiones:
 * - Los elementos no disponibles se envían con `available: false`: el motor no los ofrece, pero no se pierden.
 * - Las recomendaciones sin situación o sin un elemento de la oferta no se envían.
 * - Todos los planes (o el catálogo) usan el mismo perfil de pago del negocio.
 * - Los ajustes internos del motor (`engine`) no se envían: el motor los deriva de la oferta.
 * - Las listas vacías y los textos opcionales en blanco se omiten (`null`).
 */
export interface ContractTranslation {
  document: BusinessConfig;
  secrets: Record<string, string>;
}

const PAYMENT_PROFILE_ID = "principal";
const SECRET_SOURCE = "secret_store";

export function toBusinessConfig(config: AssistantConfig, tenantSlug: string): ContractTranslation {
  const { business, behavior, closing, messages, payments } = config;
  const isCatalog = business.salesMode === "catalog";
  const { offerings } = config;
  const secrets: Record<string, string> = {};
  const secret = (key: string, value: string): SecretRef => {
    const ref = `${SECRET_SOURCE}:${PAYMENT_PROFILE_ID}.${key}`;
    secrets[ref] = value;
    return { secret_ref: ref };
  };

  const link = payments.paymentLinkEnabled ? payments.paymentLink.trim() : "";
  const linkRef = link ? secret("link", link) : null;
  const transferMethods = payments.transferEnabled
    ? payments.transferMethods.map((method, index) => toTransferMethod(method, (field, value) => secret(`transfer.${index}.${field}`, value)))
    : [];
  const profile: PaymentProfile = {
    id: PAYMENT_PROFILE_ID,
    link: linkRef,
    transfer_enabled: transferMethods.length > 0,
    transfer_methods: transferMethods,
  };

  const problems = cleanList(behavior.customerProblems);
  const discoveryQuestions = optionalList(behavior.discoveryQuestions);
  const offeredIds = new Set(offerings.map((offering) => offering.id));
  const recommendationRules: RecommendationRule[] = behavior.recommendationRules
    .filter((rule) => rule.when.trim() && offeredIds.has(rule.offeringId))
    .map((rule) => ({ when: rule.when.trim(), recommend: rule.offeringId }));
  const promotions = payments.promotions
    .filter((promotion) => promotion.name.trim() && promotion.details.trim())
    .map((promotion) => ({ name: promotion.name.trim(), details: promotion.details.trim(), valid_until: promotion.validUntil || null }));
  const primaryMotivation = behavior.primaryMotivation.trim();
  const secondaryMotivation = behavior.secondaryMotivation.trim();
  const welcomeText = messages.welcomeText.trim();
  const paymentReported = messages.paymentReportedText.trim();
  const paymentConfirmed = messages.paymentConfirmedText.trim();

  const document: BusinessConfig = {
    schema_version: SCHEMA_VERSION as BusinessConfig["schema_version"],
    tenant_slug: tenantSlug,
    identity: {
      name: business.name.trim(),
      brand_name: business.brandName.trim() || null,
      industry: business.businessType.trim(),
      description: business.description.trim(),
      value_proposition: business.valueProposition.trim(),
      differentiators: optionalList(business.differentiators),
      location: toLocation(business.location),
      service_modes: business.serviceModes.length > 0 ? [...business.serviceModes] : null,
    },
    offer: isCatalog
      ? { model: "catalog", catalog: toCatalog(offerings) }
      : { model: "plans", plans: offerings.map(toPlan) },
    terms: { conditions: cleanList(payments.conditions), promotions: promotions.length > 0 ? promotions : null },
    payments: [profile],
    sales: {
      buying_motivation: primaryMotivation ? { primary: primaryMotivation, secondary: secondaryMotivation || null } : null,
      customer_problems: problems.map((problem, index) => ({ id: `problema_${index + 1}`, impacts: [problem] })),
      benefits: optionalList(behavior.benefits),
      arguments: optionalList(behavior.sellingPoints),
      discovery: discoveryQuestions ? { questions: discoveryQuestions } : null,
      recommendation_rules: recommendationRules.length > 0 ? recommendationRules : null,
      instructions: optionalList(behavior.salesInstructions),
    },
    capabilities: {
      service_channels: [...messages.serviceChannels],
      product_channels: [],
      actions_primary: closing.actions.filter(isPrimaryAction),
      actions_support: closing.actions.filter((action) => !isPrimaryAction(action)),
      closing_methods: {
        payment_link: closing.sendPaymentLink,
        human_handoff: closing.humanHandoff,
        data_collection: closing.collectCustomerData,
      },
      data_collection: {
        enabled: closing.collectCustomerData,
        fields: closing.collectCustomerData ? (closing.customerDataFields as ("nombre" | "telefono" | "direccion" | "detalles")[]) : [],
      },
    },
    messages: {
      welcome: { enabled: messages.welcomeEnabled, text: welcomeText },
      payment_reported: paymentReported || null,
      payment_confirmed: paymentConfirmed || null,
    },
    response_style: { tone: behavior.tone.trim() || null, length: behavior.responseLength, max_words: behavior.maxWords },
    knowledge: {
      faqs: behavior.faqs
        .map((faq) => ({ question: faq.question.trim(), answer: faq.answer.trim() }))
        .filter((faq) => faq.question && faq.answer),
    },
    inventory: { items: [] },
  };
  return { document, secrets };
}

function optionalList(items: string[]): string[] | null {
  const cleaned = cleanList(items);
  return cleaned.length > 0 ? cleaned : null;
}

function toLocation(location: BusinessLocation): Location | null {
  if (location.type === "") return null;
  return {
    type: location.type,
    address: location.type === "virtual" ? null : location.address.trim() || null,
    city: location.city.trim() || null,
    coverage: { type: location.coverageType, zones: cleanList(location.coverageZones) },
  };
}

function toTransferMethod(method: TransferMethod, secret: (field: string, value: string) => SecretRef): ContractTransferMethod {
  switch (method.type) {
    case "nequi":
    case "daviplata":
      return { type: method.type, number: secret("number", method.phoneNumber.replace(/\s+/g, "")) };
    case "bank":
      return {
        type: "bank",
        bank: method.bankName.trim(),
        account_type: method.accountType,
        account_number: secret("account_number", method.accountNumber.replace(/[\s-]+/g, "")),
      };
    case "breb":
      return { type: "breb", reference: secret("reference", method.reference.trim()) };
  }
}

function toPlan(offering: Offering): Plan {
  const price: PlanPrice = { currency: offering.currency };
  if (offering.setupFee !== null) price.implementation = offering.setupFee;
  if (offering.price !== null) {
    if (offering.billing === "monthly") price.monthly = offering.price;
    else price.price = offering.price;
  }
  return {
    id: offering.id,
    name: offering.name.trim(),
    description: offering.description.trim() || null,
    prices: [price],
    includes: cleanList(offering.features),
    not_included: cleanList(offering.notIncluded),
    payment_profile: PAYMENT_PROFILE_ID,
    available: offering.available,
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

function toCatalog(offerings: Offering[]) {
  // Categorías que se escriben igual sin tildes ni mayúsculas comparten id: se conserva el primer nombre.
  const categories = new Map<string, string>();
  for (const offering of offerings) {
    const name = offering.category.trim() || "General";
    const id = categoryId(name);
    if (!categories.has(id)) categories.set(id, name);
  }
  const items: CatalogItem[] = offerings.map((offering) => ({
    id: offering.id,
    name: offering.name.trim(),
    category: categoryId(offering.category.trim() || "General"),
    description: offering.description.trim() || null,
    prices: offering.price !== null ? [{ currency: offering.currency, amount: offering.price }] : [],
    features: optionalList(offering.features),
    available: offering.available,
  }));
  return {
    categories: [...categories].map(([id, name]) => ({ id, name })),
    items,
    payment_profile: PAYMENT_PROFILE_ID,
  };
}
