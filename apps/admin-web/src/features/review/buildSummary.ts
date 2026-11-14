import { allActions, categoryName, isAvailable, isCatalog, isLinkActive, isMethodActive, joinList, offerEntries, paymentOptionCounts } from "../../domain/config/document";
import { escalationSummary } from "../../domain/assistant/escalation";
import { mainPlanAmount } from "../../domain/config/factories";
import { ASSISTANT_ACTIONS, CUSTOMER_DATA_FIELDS, labelFor, OFFER_MODELS, RESPONSE_LENGTHS, SERVICE_CHANNELS, TRANSFER_METHOD_TYPES } from "../../domain/config/options";
import type { BusinessDocument, CatalogItem, Plan } from "../../domain/config/types";
import type { ConfigSectionId } from "../../domain/sections";
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

const text = (value: string | null | undefined) => value?.trim() || EMPTY;
const list = (values: string[] | null | undefined) => joinList(values) || EMPTY;
const yesNo = (value: boolean) => (value ? "Sí" : "No");

function priceOf(document: BusinessDocument, entry: Plan | CatalogItem): string {
  if (isCatalog(document)) {
    const [price] = (entry as CatalogItem).prices;
    return price ? formatPrice(price.amount, price.currency) : "Sin precio";
  }
  const [price] = (entry as Plan).prices;
  if (!price) return "Sin precio";
  const { amount, period } = mainPlanAmount(price);
  return `${formatPrice(amount, price.currency)}${period ? ` / ${period}` : ""}`;
}

function paymentOptionsText({ active, inactive }: { active: number; inactive: number }): string {
  if (active + inactive === 0) return "Ninguno";
  if (inactive > 0) return `${active} ${active === 1 ? "activo" : "activos"} y ${inactive} ${inactive === 1 ? "inactivo" : "inactivos"}, guardados de forma segura`;
  return active === 1 ? "1 configurado, guardado de forma segura" : `${active} configurados, guardados de forma segura`;
}

/** Resumen legible del documento para la pantalla de revisión. Solo indica qué medios de pago hay, nunca sus datos. */
export function buildSummary(document: BusinessDocument): SummarySection[] {
  const { identity, payments, capabilities, response_style: style, sales, knowledge, messages, terms } = document;
  const entries = offerEntries(document);
  const available = entries.filter(isAvailable);
  const methods = payments.flatMap((profile) => (profile.transfer_methods ?? []).filter((method) => isMethodActive(profile, method)));

  return [
    {
      id: "business",
      rows: [
        { label: "Nombre comercial", value: text(identity.name) },
        { label: "A qué se dedica", value: text(identity.industry) },
        { label: "Descripción", value: text(identity.description) },
        { label: "Propuesta de valor", value: text(identity.value_proposition) },
        { label: "Forma de venta", value: labelFor(OFFER_MODELS, document.offer.model) },
      ],
    },
    {
      id: "catalog",
      rows: [
        { label: "Disponibles", value: `${available.length} de ${entries.length}` },
        ...available.map((entry) => ({
          label: entry.name.trim() || "Sin nombre",
          value: isCatalog(document) ? `${priceOf(document, entry)} · ${categoryName(document, (entry as CatalogItem).category)}` : priceOf(document, entry),
        })),
      ],
    },
    {
      id: "payments",
      rows: [
        { label: "Medios de pago", value: paymentOptionsText(paymentOptionCounts(document)) },
        { label: "Enlace de pago", value: payments.some(isLinkActive) ? "Configurado" : payments.some((profile) => profile.link) ? "Inactivo" : "Desactivado" },
        { label: "Transferencias", value: methods.length > 0 ? methods.map((method) => labelFor(TRANSFER_METHOD_TYPES, method.type)).join(" · ") : "Desactivadas" },
        { label: "Promociones", value: list(terms.promotions?.map((promotion) => promotion.name)) },
        { label: "Condiciones", value: list(terms.conditions) },
        { label: "Compartir datos de pago", value: yesNo(capabilities.closing_methods.payment_link) },
        { label: "Ofrecer atención de una persona", value: yesNo(capabilities.closing_methods.human_handoff) },
        {
          label: "Datos que pide",
          value: capabilities.data_collection.enabled ? (capabilities.data_collection.fields ?? []).map((field) => labelFor(CUSTOMER_DATA_FIELDS, field)).join(", ") || EMPTY : "Ninguno",
        },
        { label: "Acciones", value: allActions(document).map((action) => labelFor(ASSISTANT_ACTIONS, action)).join(", ") || EMPTY },
      ],
    },
    {
      id: "assistant",
      rows: [
        { label: "Tono", value: text(style.tone) },
        { label: "Respuestas", value: labelFor(RESPONSE_LENGTHS, style.length ?? "short") },
        { label: "Por qué te compran", value: list([sales.buying_motivation?.primary ?? "", sales.buying_motivation?.secondary ?? ""]) },
        { label: "Instrucciones", value: list(sales.instructions) },
        { label: "Preguntas frecuentes", value: list(knowledge.faqs?.map((faq) => faq.question)) },
        { label: "Cuándo pasa a una persona", value: escalationSummary(document) },
      ],
    },
    {
      id: "messages",
      rows: [
        { label: "Bienvenida", value: messages.welcome.enabled ? text(messages.welcome.text) : "Desactivada" },
        { label: "Al reportar un pago", value: text(messages.payment_reported) },
        { label: "Canales de atención", value: (capabilities.service_channels ?? []).map((channel) => labelFor(SERVICE_CHANNELS, channel)).join(", ") || EMPTY },
      ],
    },
  ];
}
