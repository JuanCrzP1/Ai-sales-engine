import {
  ASSISTANT_ACTIONS,
  CUSTOMER_DATA_FIELDS,
  labelFor,
  RESPONSE_LENGTHS,
  SALES_MODES,
  SERVICE_CHANNELS,
  TRANSFER_METHOD_TYPES,
} from "../../domain/config/options";
import type { AssistantConfig } from "../../domain/config/types";
import type { ConfigSectionId } from "../../domain/sections";
import { cleanList } from "../../lib/text";
import { formatPrice } from "../../lib/format";

export interface SummaryRow {
  label: string;
  value: string;
}

export interface SummarySection {
  id: ConfigSectionId;
  rows: SummaryRow[];
}

const EMPTY = "Sin definir";

const text = (value: string) => value.trim() || EMPTY;
const list = (values: string[]) => cleanList(values).join(" · ") || EMPTY;
const yesNo = (value: boolean) => (value ? "Sí" : "No");

/**
 * Resumen legible de la configuración para la pantalla de revisión.
 * No muestra números de cuenta completos: solo los cuatro últimos dígitos.
 */
export function buildSummary(config: AssistantConfig): SummarySection[] {
  const { business, offerings, payments, closing, behavior, messages } = config;
  const available = offerings.filter((offering) => offering.available);

  return [
    {
      id: "business",
      rows: [
        { label: "Nombre comercial", value: text(business.name) },
        { label: "A qué se dedica", value: text(business.businessType) },
        { label: "Propuesta de valor", value: text(business.valueProposition) },
        { label: "Forma de venta", value: labelFor(SALES_MODES, business.salesMode) },
      ],
    },
    {
      id: "catalog",
      rows: [
        { label: "Disponibles", value: `${available.length} de ${offerings.length}` },
        ...available.map((offering) => ({
          label: offering.name.trim() || "Sin nombre",
          value: formatPrice(offering.price, offering.currency),
        })),
      ],
    },
    {
      id: "payments",
      rows: [
        { label: "Enlace de pago", value: payments.paymentLinkEnabled ? text(payments.paymentLink) : "Desactivado" },
        {
          label: "Transferencias",
          value: payments.transferEnabled
            ? payments.transferMethods.map((method) => `${labelFor(TRANSFER_METHOD_TYPES, method.type)} ${maskedAccount(method)}`.trim()).join(" · ") || EMPTY
            : "Desactivadas",
        },
        { label: "Condiciones", value: list(payments.conditions) },
        { label: "Compartir datos de pago", value: yesNo(closing.sendPaymentLink) },
        { label: "Ofrecer atención de una persona", value: yesNo(closing.humanHandoff) },
        {
          label: "Datos que pide",
          value: closing.collectCustomerData ? closing.customerDataFields.map((field) => labelFor(CUSTOMER_DATA_FIELDS, field)).join(", ") || EMPTY : "No pide datos",
        },
        { label: "Acciones", value: closing.actions.map((action) => labelFor(ASSISTANT_ACTIONS, action)).join(", ") || EMPTY },
      ],
    },
    {
      id: "assistant",
      rows: [
        { label: "Respuestas", value: labelFor(RESPONSE_LENGTHS, behavior.responseLength) },
        { label: "Por qué te compran", value: list([behavior.primaryMotivation, behavior.secondaryMotivation]) },
        { label: "Problemas que resuelves", value: list(behavior.customerProblems) },
        { label: "Preguntas frecuentes", value: list(behavior.faqs.map((faq) => faq.question)) },
      ],
    },
    {
      id: "messages",
      rows: [
        { label: "Bienvenida", value: messages.welcomeEnabled ? text(messages.welcomeText) : "Desactivada" },
        { label: "Al reportar un pago", value: text(messages.paymentReportedText) },
        { label: "Canales de atención", value: messages.serviceChannels.map((channel) => labelFor(SERVICE_CHANNELS, channel)).join(", ") || EMPTY },
      ],
    },
  ];
}

function maskedAccount(method: AssistantConfig["payments"]["transferMethods"][number]): string {
  const raw = method.type === "bank" ? method.accountNumber : method.type === "breb" ? method.reference : method.phoneNumber;
  const digits = raw.replace(/\s+/g, "");
  if (!digits) return "";
  return method.type === "breb" ? "(referencia configurada)" : `terminada en ${digits.slice(-4)}`;
}
