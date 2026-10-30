import {
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
import type { AssistantConfig, Offering, TransferMethod } from "../config/types";
import type { ConfigSectionId } from "../sections";
import { localIsoDate } from "../../lib/format";
import { cleanList, countWords } from "../../lib/text";
import {
  isAccountNumber,
  isBlank,
  isColombianMobile,
  isHttpUrl,
  isHttpsUrl,
  isPositiveAmount,
} from "./fieldChecks";
import type { ValidationIssue } from "./types";

/**
 * Reglas de validación de la configuración. Única fuente de verdad: los formularios,
 * el inicio y la revisión consumen el resultado de `validateConfig`.
 */
export function validateConfig(config: AssistantConfig, today: Date = new Date()): ValidationIssue[] {
  return [
    ...validateBusiness(config),
    ...validateCatalog(config),
    ...validatePayments(config, localIsoDate(today)),
    ...validateAssistant(config),
    ...validateMessages(config),
  ];
}

/** Listas del perfil comercial: el contrato admite hasta MAX_PROFILE_ITEMS frases de MAX_PROFILE_ITEM_CHARS. */
function validateList(section: ConfigSectionId, field: string, label: string, items: string[]): ValidationIssue[] {
  const cleaned = cleanList(items);
  const issues: ValidationIssue[] = [];
  if (cleaned.length > MAX_PROFILE_ITEMS) {
    issues.push({ section, field, severity: "error", message: `${label}: puedes agregar hasta ${MAX_PROFILE_ITEMS}.` });
  }
  if (cleaned.some((item) => item.length > MAX_PROFILE_ITEM_CHARS)) {
    issues.push({ section, field, severity: "error", message: `${label}: cada uno admite hasta ${MAX_PROFILE_ITEM_CHARS} caracteres.` });
  }
  return issues;
}

function validateBusiness({ business }: AssistantConfig): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const add = (field: string, severity: ValidationIssue["severity"], message: string) =>
    issues.push({ section: "business", field: `business.${field}`, severity, message });

  if (isBlank(business.name)) add("name", "error", "Escribe el nombre comercial de tu negocio.");
  if (isBlank(business.description)) {
    add("description", "error", "Describe brevemente tu negocio.");
  } else if (countWords(business.description) > WORD_LIMITS.description) {
    add("description", "warning", `El asistente usa las primeras ${WORD_LIMITS.description} palabras de la descripción.`);
  }
  if (isBlank(business.businessType)) {
    add("businessType", "error", "Indica a qué se dedica tu negocio.");
  } else if (countWords(business.businessType) > WORD_LIMITS.businessType) {
    add(
      "businessType",
      "warning",
      `El asistente solo usa las primeras ${WORD_LIMITS.businessType} palabras. Intenta resumirlo.`,
    );
  }
  if (isBlank(business.valueProposition)) {
    add("valueProposition", "error", "Escribe tu propuesta de valor: qué gana el cliente contigo.");
  } else if (countWords(business.valueProposition) > WORD_LIMITS.valueProposition) {
    add(
      "valueProposition",
      "warning",
      `El asistente solo usa las primeras ${WORD_LIMITS.valueProposition} palabras; el resto se corta.`,
    );
  }
  issues.push(...validateList("business", "business.differentiators", "Diferenciadores", business.differentiators));
  const { location } = business;
  if ((location.type === "fisico" || location.type === "mixto") && isBlank(location.address)) {
    add("location.address", "warning", "Sin dirección, el asistente no podrá decir dónde queda tu local.");
  }
  if (location.type !== "") {
    issues.push(...validateList("business", "business.location.coverageZones", "Zonas de cobertura", location.coverageZones));
  }
  return issues;
}

function validateCatalog(config: AssistantConfig): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const isCatalog = config.business.salesMode === "catalog";

  if (!config.offerings.some((offering) => offering.available)) {
    issues.push({
      section: "catalog",
      field: "offerings",
      severity: "error",
      message: "Agrega al menos un producto o servicio disponible.",
    });
  }

  for (const offering of config.offerings) {
    issues.push(...validateOffering(offering, isCatalog));
  }
  return issues;
}

export function validateOffering(offering: Offering, isCatalog: boolean): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const add = (field: string, severity: ValidationIssue["severity"], message: string) =>
    issues.push({ section: "catalog", field: `offerings.${offering.id}.${field}`, severity, message });
  const label = offering.name.trim() || "Un elemento sin nombre";

  if (isBlank(offering.name)) add("name", "error", "Cada producto o servicio necesita un nombre.");
  if (!isPositiveAmount(offering.price)) add("price", "error", `${label}: indica un precio mayor que cero.`);
  if (offering.setupFee !== null && !isPositiveAmount(offering.setupFee)) {
    add("setupFee", "error", `${label}: el costo inicial debe ser mayor que cero o quedar vacío.`);
  }
  if (isCatalog && isBlank(offering.category)) {
    add("category", "error", `${label}: elige o escribe una categoría.`);
  }
  if (countWords(offering.description) > WORD_LIMITS.offeringDescription) {
    add("description", "warning", `${label}: el asistente usa las primeras ${WORD_LIMITS.offeringDescription} palabras de la descripción.`);
  }
  if (isCatalog) {
    issues.push(...validateList("catalog", `offerings.${offering.id}.features`, `${label}, características`, offering.features));
  }
  return issues;
}

function validatePayments({ payments, closing }: AssistantConfig, todayIso: string): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const add = (field: string, severity: ValidationIssue["severity"], message: string) =>
    issues.push({ section: "payments", field, severity, message });

  const hasLink = payments.paymentLinkEnabled && !isBlank(payments.paymentLink);
  if (payments.paymentLinkEnabled) {
    if (isBlank(payments.paymentLink)) {
      add("payments.paymentLink", "error", "Pega el enlace de pago o desactiva esta opción.");
    } else if (!isHttpUrl(payments.paymentLink)) {
      add("payments.paymentLink", "error", "El enlace debe ser una dirección web válida (https://…).");
    } else if (!isHttpsUrl(payments.paymentLink)) {
      add("payments.paymentLink", "warning", "Usa un enlace seguro que empiece por https://.");
    }
  }

  if (payments.transferEnabled && payments.transferMethods.length === 0) {
    add("payments.transferMethods", "error", "Agrega al menos una cuenta o desactiva las transferencias.");
  }
  if (payments.transferEnabled) {
    for (const method of payments.transferMethods) issues.push(...validateTransferMethod(method));
    const types = payments.transferMethods.map((method) => method.type);
    if (new Set(types).size !== types.length) {
      add(
        "payments.transferMethods.duplicates",
        "warning",
        "Hay dos cuentas del mismo tipo: el asistente solo comparte la primera de cada tipo.",
      );
    }
  }

  const hasTransfer = payments.transferEnabled && payments.transferMethods.length > 0;
  if (!hasLink && !hasTransfer) {
    add("payments", "warning", "No hay ningún medio de pago: el asistente no podrá indicar cómo pagar.");
  }

  if (!closing.sendPaymentLink && !closing.humanHandoff && !closing.collectCustomerData) {
    add("closing.methods", "error", "Activa al menos una forma de cerrar la venta.");
  }
  if (closing.sendPaymentLink && !hasLink && !hasTransfer) {
    add("closing.sendPaymentLink", "warning", "Activaste el cierre con pago, pero no hay enlace ni cuentas configuradas.");
  }
  if (closing.sendPaymentLink && !hasLink && hasTransfer) {
    add("closing.sendPaymentLink", "warning", "No hay enlace de pago: el asistente ofrecerá solo transferencias.");
  }
  if (closing.collectCustomerData && closing.customerDataFields.length === 0) {
    add("closing.customerDataFields", "error", "Elige qué datos puede pedir el asistente.");
  }
  if (closing.humanHandoff) {
    add(
      "closing.humanHandoff",
      "warning",
      "El asistente podrá ofrecer pasar a una persona, pero esta versión aún no avisa a nadie de tu equipo.",
    );
  }
  if (closing.actions.length === 0) {
    add("closing.actions", "error", "Elige al menos una acción que pueda realizar el asistente.");
  }

  if (payments.promotions.length > MAX_PROMOTIONS) {
    add("payments.promotions", "error", `Puedes guardar hasta ${MAX_PROMOTIONS} promociones.`);
  }
  for (const promotion of payments.promotions) {
    const field = (name: string) => `payments.promotions.${promotion.id}.${name}`;
    if (isBlank(promotion.name)) add(field("name"), "error", "Escribe el nombre de la promoción o elimínala.");
    else if (promotion.name.trim().length > MAX_PROFILE_ITEM_CHARS) add(field("name"), "error", `El nombre admite hasta ${MAX_PROFILE_ITEM_CHARS} caracteres.`);
    if (isBlank(promotion.details)) add(field("details"), "error", "Explica en qué consiste la promoción.");
    else if (promotion.details.trim().length > MAX_PROFILE_ITEM_CHARS) add(field("details"), "error", `El detalle admite hasta ${MAX_PROFILE_ITEM_CHARS} caracteres.`);
    if (promotion.validUntil && !/^\d{4}-\d{2}-\d{2}$/.test(promotion.validUntil)) {
      add(field("validUntil"), "error", "Escribe una fecha válida o déjala vacía.");
    } else if (promotion.validUntil && promotion.validUntil < todayIso) {
      add(field("validUntil"), "warning", "Esta promoción ya venció: el asistente no la ofrecerá.");
    }
  }
  return issues;
}

export function validateTransferMethod(method: TransferMethod): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const add = (field: string, message: string) =>
    issues.push({
      section: "payments",
      field: `payments.transfer.${method.id}.${field}`,
      severity: "error",
      message,
    });

  switch (method.type) {
    case "nequi":
    case "daviplata":
      if (!isColombianMobile(method.phoneNumber)) add("phoneNumber", "Escribe un celular de 10 dígitos que empiece por 3.");
      break;
    case "bank":
      if (isBlank(method.bankName)) add("bankName", "Escribe el nombre del banco.");
      if (!isAccountNumber(method.accountNumber)) add("accountNumber", "Escribe un número de cuenta válido (solo dígitos).");
      break;
    case "breb":
      if (isBlank(method.reference)) add("reference", "Escribe tu llave o referencia Bre-B.");
      break;
  }
  return issues;
}

function validateAssistant({ behavior, offerings }: AssistantConfig): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const add = (field: string, severity: ValidationIssue["severity"], message: string) =>
    issues.push({ section: "assistant", field: `behavior.${field}`, severity, message });

  if (behavior.tone.trim().length > MAX_TONE_CHARS) add("tone", "error", `El tono admite hasta ${MAX_TONE_CHARS} caracteres.`);
  if (behavior.maxWords !== null) {
    const [low, high] = RESPONSE_LENGTH_WORD_RANGES[behavior.responseLength];
    if (!Number.isInteger(behavior.maxWords) || behavior.maxWords < low || (high !== null && behavior.maxWords > high)) {
      const label = labelFor(RESPONSE_LENGTHS, behavior.responseLength).toLowerCase();
      const range = high !== null ? `entre ${low} y ${high}` : `de al menos ${low}`;
      add("maxWords", "error", `Con respuestas ${label}, el límite debe ser ${range} palabras.`);
    }
  }
  issues.push(
    ...validateList("assistant", "behavior.benefits", "Beneficios", behavior.benefits),
    ...validateList("assistant", "behavior.sellingPoints", "Argumentos de venta", behavior.sellingPoints),
    ...validateList("assistant", "behavior.discoveryQuestions", "Preguntas para entender al cliente", behavior.discoveryQuestions),
    ...validateList("assistant", "behavior.salesInstructions", "Instrucciones de venta", behavior.salesInstructions),
  );

  if (behavior.recommendationRules.length > MAX_PROFILE_ITEMS) {
    add("recommendationRules", "error", `Puedes agregar hasta ${MAX_PROFILE_ITEMS} recomendaciones.`);
  }
  for (const rule of behavior.recommendationRules) {
    const field = (name: string) => `recommendationRules.${rule.id}.${name}`;
    const offering = offerings.find((item) => item.id === rule.offeringId);
    if (isBlank(rule.when)) add(field("when"), "error", "Describe la situación del cliente o elimina la recomendación.");
    else if (rule.when.trim().length > MAX_PROFILE_ITEM_CHARS) add(field("when"), "error", `La situación admite hasta ${MAX_PROFILE_ITEM_CHARS} caracteres.`);
    if (!offering) add(field("offeringId"), "error", "Elige qué plan o producto recomendar.");
    else if (!offering.available) {
      add(field("offeringId"), "warning", `"${offering.name.trim() || "Este elemento"}" no está disponible: el asistente no lo recomendará.`);
    }
  }

  if (behavior.customerProblems.length === 0 && isBlank(behavior.primaryMotivation)) {
    issues.push({
      section: "assistant",
      field: "behavior.customerProblems",
      severity: "warning",
      message: "Cuéntale al asistente qué problemas resuelves o por qué te compran; le ayuda a vender mejor.",
    });
  }
  if (behavior.faqs.length > MAX_FAQS) {
    issues.push({ section: "assistant", field: "behavior.faqs", severity: "error", message: `Puedes guardar hasta ${MAX_FAQS} preguntas frecuentes.` });
  }
  for (const faq of behavior.faqs) {
    const add = (field: string, message: string) =>
      issues.push({ section: "assistant", field: `behavior.faqs.${faq.id}.${field}`, severity: "error", message });
    if (isBlank(faq.question)) add("question", "Escribe la pregunta o elimínala.");
    else if (faq.question.trim().length > MAX_FAQ_QUESTION_CHARS) add("question", `La pregunta admite hasta ${MAX_FAQ_QUESTION_CHARS} caracteres.`);
    if (isBlank(faq.answer)) add("answer", "Escribe la respuesta o elimina la pregunta.");
    else if (faq.answer.trim().length > MAX_FAQ_ANSWER_CHARS) add("answer", `La respuesta admite hasta ${MAX_FAQ_ANSWER_CHARS} caracteres.`);
  }
  return issues;
}

function validateMessages({ messages }: AssistantConfig): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  if (messages.welcomeEnabled && isBlank(messages.welcomeText)) {
    issues.push({
      section: "messages",
      field: "messages.welcomeText",
      severity: "error",
      message: "Escribe el mensaje de bienvenida o desactívalo.",
    });
  }
  if (isBlank(messages.paymentReportedText)) {
    issues.push({
      section: "messages",
      field: "messages.paymentReportedText",
      severity: "warning",
      message: "Sin este mensaje, el asistente responderá con sus propias palabras cuando el cliente diga que ya pagó.",
    });
  }
  if (messages.serviceChannels.length === 0) {
    issues.push({
      section: "messages",
      field: "messages.serviceChannels",
      severity: "warning",
      message: "Elige al menos un canal de atención para que el asistente sepa por dónde atiendes.",
    });
  }
  return issues;
}
