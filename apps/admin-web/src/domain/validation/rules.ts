import { WORD_LIMITS } from "../config/engineUsage";
import type { AssistantConfig, Offering, TransferMethod } from "../config/types";
import { countWords } from "../../lib/text";
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
export function validateConfig(config: AssistantConfig): ValidationIssue[] {
  return [
    ...validateBusiness(config),
    ...validateCatalog(config),
    ...validatePayments(config),
    ...validateAssistant(config),
    ...validateMessages(config),
  ];
}

function validateBusiness({ business }: AssistantConfig): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const add = (field: string, severity: ValidationIssue["severity"], message: string) =>
    issues.push({ section: "business", field: `business.${field}`, severity, message });

  if (isBlank(business.name)) add("name", "error", "Escribe el nombre comercial de tu negocio.");
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
  return issues;
}

function validatePayments({ payments, closing }: AssistantConfig): ValidationIssue[] {
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

function validateAssistant({ behavior }: AssistantConfig): ValidationIssue[] {
  if (behavior.customerProblems.length === 0 && isBlank(behavior.primaryMotivation)) {
    return [
      {
        section: "assistant",
        field: "behavior.customerProblems",
        severity: "warning",
        message: "Cuéntale al asistente qué problemas resuelves o por qué te compran; le ayuda a vender mejor.",
      },
    ];
  }
  return [];
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
