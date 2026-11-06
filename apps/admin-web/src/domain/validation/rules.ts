import type { CatalogItem, Plan } from "../../contracts/businessConfig.v1";
import { paymentHolders, isAvailable, isCatalog, isLinkActive, isMethodActive, isStoredRef, offerEntries } from "../config/document";
import {
  MAX_CATEGORIES_USED,
  MAX_FAQ_ANSWER_CHARS,
  MAX_FAQ_QUESTION_CHARS,
  MAX_FAQS,
  MAX_PROFILE_ITEM_CHARS,
  MAX_PROFILE_ITEMS,
  MAX_PROMOTIONS,
  MAX_TONE_CHARS,
  RESPONSE_LENGTH_WORD_RANGES,
  WORD_LIMITS,
} from "../config/engineLimits";
import { labelFor, RESPONSE_LENGTHS } from "../config/options";
import type { BusinessDocument, PaymentValues, WorkingCopy } from "../config/types";
import type { ConfigSectionId } from "../sections";
import { localIsoDate } from "../../lib/format";
import { cleanList, countWords } from "../../lib/text";
import { isAccountNumber, isBlank, isColombianMobile, isHttpsUrl, isHttpUrl, isPositiveAmount } from "./fieldChecks";
import type { ValidationIssue } from "./types";

/**
 * Validación anticipada para ayudar mientras se edita. No es la autoridad: el servidor valida de nuevo con el contrato
 * (BusinessConfig v1) al guardar y sus errores se muestran en los mismos campos. Los límites vienen del contrato generado.
 */
export function validateDocument({ document, paymentValues }: WorkingCopy, today: Date = new Date()): ValidationIssue[] {
  return [
    ...validateBusiness(document),
    ...validateOffer(document),
    ...validatePayments(document, paymentValues, localIsoDate(today)),
    ...validateAssistant(document),
    ...validateMessages(document),
  ];
}

/** Listas del perfil comercial: el contrato admite hasta MAX_PROFILE_ITEMS frases de MAX_PROFILE_ITEM_CHARS. */
function validateList(section: ConfigSectionId, field: string, label: string, items: string[] | null | undefined): ValidationIssue[] {
  const cleaned = cleanList(items ?? []);
  const issues: ValidationIssue[] = [];
  if (cleaned.length > MAX_PROFILE_ITEMS) {
    issues.push({ section, field, severity: "error", message: `${label}: puedes agregar hasta ${MAX_PROFILE_ITEMS}.` });
  }
  if (cleaned.some((item) => item.length > MAX_PROFILE_ITEM_CHARS)) {
    issues.push({ section, field, severity: "error", message: `${label}: cada uno admite hasta ${MAX_PROFILE_ITEM_CHARS} caracteres.` });
  }
  return issues;
}

function validateBusiness({ identity }: BusinessDocument): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const add = (field: string, severity: ValidationIssue["severity"], message: string) =>
    issues.push({ section: "business", field: `identity.${field}`, severity, message });

  if (isBlank(identity.name)) add("name", "error", "Escribe el nombre comercial de tu negocio.");
  if (isBlank(identity.description)) {
    add("description", "error", "Describe brevemente tu negocio.");
  } else if (countWords(identity.description) > WORD_LIMITS.description) {
    add("description", "warning", `El asistente usa las primeras ${WORD_LIMITS.description} palabras de la descripción.`);
  }
  if (isBlank(identity.industry)) {
    add("industry", "error", "Indica a qué se dedica tu negocio.");
  } else if (countWords(identity.industry) > WORD_LIMITS.businessType) {
    add("industry", "warning", `El asistente solo usa las primeras ${WORD_LIMITS.businessType} palabras. Intenta resumirlo.`);
  }
  if (isBlank(identity.value_proposition)) {
    add("value_proposition", "error", "Escribe tu propuesta de valor: qué gana el cliente contigo.");
  } else if (countWords(identity.value_proposition) > WORD_LIMITS.valueProposition) {
    add("value_proposition", "warning", `El asistente solo usa las primeras ${WORD_LIMITS.valueProposition} palabras; el resto se corta.`);
  }
  issues.push(
    ...validateList("business", "identity.differentiators", "Diferenciadores", identity.differentiators),
    ...validateList("business", "identity.credibility", "Pruebas de confianza", identity.credibility),
  );
  const location = identity.location;
  if (location && (location.type === "fisico" || location.type === "mixto") && isBlank(location.address ?? "")) {
    add("location.address", "warning", "Sin dirección, el asistente no podrá decir dónde queda tu local.");
  }
  if (location) issues.push(...validateList("business", "identity.location.coverage.zones", "Zonas de cobertura", location.coverage?.zones));
  return issues;
}

function validateOffer(document: BusinessDocument): ValidationIssue[] {
  const catalog = isCatalog(document);
  const prefix = catalog ? "offer.catalog.items" : "offer.plans";
  const entries = offerEntries(document);
  const issues: ValidationIssue[] = [];
  if (!entries.some(isAvailable)) {
    issues.push({ section: "catalog", field: "offer", severity: "error", message: "Agrega al menos un producto o servicio disponible." });
  }
  const categories = document.offer.catalog?.categories.length ?? 0;
  if (categories > MAX_CATEGORIES_USED) {
    issues.push({ section: "catalog", field: "offer.catalog.categories", severity: "warning", message: `Tienes ${categories} categorías: el asistente solo menciona las primeras ${MAX_CATEGORIES_USED}.` });
  }
  entries.forEach((entry, index) => {
    issues.push(...validateEntry(entry, catalog).map((issue) => ({ ...issue, field: `${prefix}.${index}.${issue.field}` })));
  });
  return issues;
}

/** Validación de un plan o producto; `field` es relativo al elemento, para usarla también en el formulario de edición. */
export function validateEntry(entry: Plan | CatalogItem, catalog: boolean, categoryName?: string): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const add = (field: string, severity: ValidationIssue["severity"], message: string) => issues.push({ section: "catalog", field, severity, message });
  const label = entry.name.trim() || "Un elemento sin nombre";

  if (isBlank(entry.name)) add("name", "error", "Cada producto o servicio necesita un nombre.");
  if (catalog) {
    const item = entry as CatalogItem;
    if (categoryName !== undefined && isBlank(categoryName)) add("category", "error", `${label}: elige o escribe una categoría.`);
    if (categoryName === undefined && isBlank(item.category)) add("category", "error", `${label}: elige o escribe una categoría.`);
    if (item.prices.length === 0 || item.prices.some((price) => !isPositiveAmount(price.amount))) add("prices", "error", `${label}: indica un precio mayor que cero.`);
    issues.push(...validateList("catalog", "features", `${label}, características`, item.features));
  } else {
    const plan = entry as Plan;
    const hasAmount = (price: Plan["prices"][number]) => [price.price, price.monthly, price.annual, price.implementation, price.first_payment].some((amount) => isPositiveAmount(amount ?? null));
    if (plan.prices.length === 0 || !plan.prices.every(hasAmount)) add("prices", "error", `${label}: indica un precio mayor que cero.`);
  }
  const currencies = entry.prices.map((price) => price.currency);
  if (new Set(currencies).size !== currencies.length) add("prices", "error", `${label}: hay dos precios en la misma moneda.`);
  if (countWords(entry.description ?? "") > WORD_LIMITS.offeringDescription) {
    add("description", "warning", `${label}: el asistente usa las primeras ${WORD_LIMITS.offeringDescription} palabras de la descripción.`);
  }
  return issues;
}

/** Formato de los datos de pago nuevos, para avisar mientras se escribe. La autoridad es el servidor (`payment_data.py`), que aplica las mismas reglas antes de guardar. */
export function validatePaymentValues({ document, paymentValues }: WorkingCopy): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  for (const holder of paymentHolders(document.payments)) {
    const value = paymentValues[holder.ref.secret_ref];
    // Un dato ya guardado con el campo de reemplazo vacío no es un error: se conserva el que hay.
    if (value === undefined || (isStoredRef(holder.ref.secret_ref) && isBlank(value))) continue;
    const add = (severity: ValidationIssue["severity"], message: string) => issues.push({ section: "payments", field: holder.path, severity, message });
    switch (holder.kind) {
      case "link":
        if (isBlank(value)) add("error", "Pega el enlace de pago o desactiva esta opción.");
        else if (!isHttpUrl(value)) add("error", "El enlace debe ser una dirección web válida (https://…).");
        else if (!isHttpsUrl(value)) add("warning", "Usa un enlace seguro que empiece por https://.");
        break;
      case "mobile":
        if (!isColombianMobile(value)) add("error", "Escribe un celular de 10 dígitos que empiece por 3.");
        break;
      case "account":
        if (!isAccountNumber(value)) add("error", "Escribe un número de cuenta válido (solo dígitos).");
        break;
      case "reference":
        if (isBlank(value)) add("error", "Escribe tu llave o referencia Bre-B.");
        break;
    }
  }
  return issues;
}

function validatePayments(document: BusinessDocument, paymentValues: PaymentValues, todayIso: string): ValidationIssue[] {
  const { payments, capabilities, terms } = document;
  const issues: ValidationIssue[] = validatePaymentValues({ document, paymentValues });
  const add = (field: string, severity: ValidationIssue["severity"], message: string) => issues.push({ section: "payments", field, severity, message });

  const hasLink = payments.some(isLinkActive);
  const hasTransfer = payments.some((profile) => (profile.transfer_methods ?? []).some((method) => isMethodActive(profile, method)));
  payments.forEach((profile, index) => {
    const methods = profile.transfer_methods ?? [];
    if (profile.transfer_enabled && methods.length === 0) {
      add(`payments.${index}.transfer_methods`, "error", "Agrega al menos una cuenta o desactiva las transferencias.");
    } else if (profile.transfer_enabled && !methods.some((method) => isMethodActive(profile, method))) {
      add(`payments.${index}.transfer_methods`, "warning", "Todas las cuentas están inactivas: el asistente no ofrecerá transferencias.");
    }
    methods.forEach((method, position) => {
      if (method.type === "bank" && isBlank(method.bank ?? "")) add(`payments.${index}.transfer_methods.${position}.bank`, "error", "Escribe el nombre del banco.");
    });
    const types = methods.filter((method) => isMethodActive(profile, method)).map((method) => method.type);
    if (new Set(types).size !== types.length) {
      add(`payments.${index}.transfer_methods.duplicates`, "warning", "Hay dos cuentas del mismo tipo: el asistente solo comparte la primera de cada tipo.");
    }
  });
  if (!hasLink && !hasTransfer) add("payments", "warning", "No hay ningún medio de pago: el asistente no podrá indicar cómo pagar.");

  const closing = capabilities.closing_methods;
  if (!closing.payment_link && !closing.human_handoff && !closing.data_collection) {
    add("capabilities.closing_methods", "error", "Activa al menos una forma de cerrar la venta.");
  }
  if (closing.payment_link && !hasLink && !hasTransfer) {
    add("capabilities.closing_methods.payment_link", "warning", "Activaste el cierre con pago, pero no hay enlace ni cuentas configuradas.");
  } else if (closing.payment_link && !hasLink) {
    add("capabilities.closing_methods.payment_link", "warning", "No hay enlace de pago: el asistente ofrecerá solo transferencias.");
  }
  if (capabilities.data_collection.enabled && (capabilities.data_collection.fields ?? []).length === 0) {
    add("capabilities.data_collection", "error", "Elige qué datos puede pedir el asistente.");
  }
  if (closing.human_handoff) {
    add("capabilities.closing_methods.human_handoff", "warning", "El asistente podrá ofrecer pasar a una persona, pero esta versión aún no avisa a nadie de tu equipo.");
  }
  if ((capabilities.actions_primary ?? []).length + (capabilities.actions_support ?? []).length === 0) {
    add("capabilities.actions", "error", "Elige al menos una acción que pueda realizar el asistente.");
  }

  const promotions = terms.promotions ?? [];
  if (promotions.length > MAX_PROMOTIONS) add("terms.promotions", "error", `Puedes guardar hasta ${MAX_PROMOTIONS} promociones.`);
  promotions.forEach((promotion, index) => {
    const field = (name: string) => `terms.promotions.${index}.${name}`;
    if (isBlank(promotion.name)) add(field("name"), "error", "Escribe el nombre de la promoción o elimínala.");
    else if (promotion.name.length > MAX_PROFILE_ITEM_CHARS) add(field("name"), "error", `El nombre admite hasta ${MAX_PROFILE_ITEM_CHARS} caracteres.`);
    if (isBlank(promotion.details)) add(field("details"), "error", "Explica en qué consiste la promoción.");
    else if (promotion.details.length > MAX_PROFILE_ITEM_CHARS) add(field("details"), "error", `El detalle admite hasta ${MAX_PROFILE_ITEM_CHARS} caracteres.`);
    if (promotion.valid_until && promotion.valid_until < todayIso) add(field("valid_until"), "warning", "Esta promoción ya venció: el asistente no la ofrecerá.");
  });
  return issues;
}

function validateAssistant(document: BusinessDocument): ValidationIssue[] {
  const { response_style: style, sales, knowledge } = document;
  const issues: ValidationIssue[] = [];
  const add = (field: string, severity: ValidationIssue["severity"], message: string) => issues.push({ section: "assistant", field, severity, message });

  if ((style.tone ?? "").length > MAX_TONE_CHARS) add("response_style.tone", "error", `El tono admite hasta ${MAX_TONE_CHARS} caracteres.`);
  if ((style.voice ?? "").length > MAX_TONE_CHARS) add("response_style.voice", "error", `La personalidad admite hasta ${MAX_TONE_CHARS} caracteres.`);
  if (style.max_words !== null && style.max_words !== undefined) {
    const length = style.length ?? "short";
    const [low, high] = RESPONSE_LENGTH_WORD_RANGES[length];
    if (!Number.isInteger(style.max_words) || style.max_words < low || (high !== null && style.max_words > high)) {
      const range = high !== null ? `entre ${low} y ${high}` : `de al menos ${low}`;
      add("response_style.max_words", "error", `Con respuestas ${labelFor(RESPONSE_LENGTHS, length).toLowerCase()}, el límite debe ser ${range} palabras.`);
    }
  }
  issues.push(
    ...validateList("assistant", "response_style.instructions", "Indicaciones de estilo", style.instructions),
    ...validateList("assistant", "sales.benefits", "Beneficios", sales.benefits),
    ...validateList("assistant", "sales.arguments", "Argumentos de venta", sales.arguments),
    ...validateList("assistant", "sales.discovery.questions", "Preguntas para entender al cliente", sales.discovery?.questions),
    ...validateList("assistant", "sales.instructions", "Instrucciones de venta", sales.instructions),
  );

  const rules = sales.recommendation_rules ?? [];
  if (rules.length > MAX_PROFILE_ITEMS) add("sales.recommendation_rules", "error", `Puedes agregar hasta ${MAX_PROFILE_ITEMS} recomendaciones.`);
  const entries = offerEntries(document);
  rules.forEach((rule, index) => {
    const field = (name: string) => `sales.recommendation_rules.${index}.${name}`;
    if (isBlank(rule.when)) add(field("when"), "error", "Describe la situación del cliente o elimina la recomendación.");
    if (isBlank(rule.recommend)) add(field("recommend"), "error", "Elige qué plan o producto recomendar.");
    else if (entries.some((entry) => entry.id === rule.recommend && !isAvailable(entry))) add(field("recommend"), "warning", "Ese elemento no está disponible: el asistente no lo recomendará.");
  });

  if ((sales.customer_problems ?? []).length === 0 && !sales.buying_motivation?.primary) {
    add("sales.customer_problems", "warning", "Cuéntale al asistente qué problemas resuelves o por qué te compran; le ayuda a vender mejor.");
  }
  const faqs = knowledge.faqs ?? [];
  if (faqs.length > MAX_FAQS) add("knowledge.faqs", "error", `Puedes guardar hasta ${MAX_FAQS} preguntas frecuentes.`);
  faqs.forEach((faq, index) => {
    const field = (name: string) => `knowledge.faqs.${index}.${name}`;
    if (isBlank(faq.question)) add(field("question"), "error", "Escribe la pregunta o elimínala.");
    else if (faq.question.length > MAX_FAQ_QUESTION_CHARS) add(field("question"), "error", `La pregunta admite hasta ${MAX_FAQ_QUESTION_CHARS} caracteres.`);
    if (isBlank(faq.answer)) add(field("answer"), "error", "Escribe la respuesta o elimina la pregunta.");
    else if (faq.answer.length > MAX_FAQ_ANSWER_CHARS) add(field("answer"), "error", `La respuesta admite hasta ${MAX_FAQ_ANSWER_CHARS} caracteres.`);
  });
  return issues;
}

function validateMessages({ messages, capabilities }: BusinessDocument): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  if (messages.welcome.enabled && isBlank(messages.welcome.text ?? "")) {
    issues.push({ section: "messages", field: "messages.welcome.text", severity: "error", message: "Escribe el mensaje de bienvenida o desactívalo." });
  }
  if (isBlank(messages.payment_reported ?? "")) {
    issues.push({
      section: "messages",
      field: "messages.payment_reported",
      severity: "warning",
      message: "Sin este mensaje, el asistente responderá con sus propias palabras cuando el cliente diga que ya pagó.",
    });
  }
  if ((capabilities.service_channels ?? []).length === 0) {
    issues.push({ section: "messages", field: "capabilities.service_channels", severity: "warning", message: "Elige al menos un canal de atención para que el asistente sepa por dónde atiendes." });
  }
  return issues;
}
