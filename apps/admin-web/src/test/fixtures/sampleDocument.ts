import type { BusinessDocument } from "../../domain/config/types";
import sample from "./sampleContractDocument.json";

/**
 * Documento completo de un negocio ficticio, solo para pruebas. Es el mismo archivo que el contrato valida en
 * `tests/test_business_config_contract.py`: si deja de cumplirlo, fallan esas pruebas.
 */
export const SAMPLE_DOCUMENT = sample as unknown as BusinessDocument;

/** Otro negocio ficticio, que vende por planes y no tiene datos de pago. Las pruebas de integración lo guardan en la API real. */
export const SAMPLE_PLANS_DOCUMENT: BusinessDocument = {
  schema_version: "1.0" as BusinessDocument["schema_version"],
  tenant_slug: "software_norte",
  identity: {
    name: "Software Norte",
    industry: "software de facturación",
    description: "Programa de facturación para tiendas de barrio.",
    value_proposition: "Factura desde el celular sin aprender contabilidad.",
  },
  offer: {
    model: "plans",
    plans: [
      { id: "basico", name: "Básico", prices: [{ currency: "COP", monthly: 50000 }], includes: ["Soporte por chat"], not_included: ["Capacitación"], available: true },
      { id: "pro", name: "Pro", prices: [{ currency: "COP", monthly: 90000 }], includes: ["Soporte telefónico"], not_included: [], available: false },
    ],
  },
  terms: {},
  payments: [],
  sales: {},
  capabilities: {
    service_channels: ["whatsapp"],
    product_channels: [],
    actions_primary: ["cerrar_venta"],
    actions_support: ["responder_dudas"],
    closing_methods: { payment_link: false, human_handoff: false, data_collection: true },
    data_collection: { enabled: true, fields: ["nombre", "telefono"] },
  },
  messages: { welcome: { enabled: false, text: "" }, payment_reported: "Gracias, reviso tu pago." },
  response_style: { length: "short" },
  knowledge: { faqs: [{ question: "¿Tiene permanencia?", answer: "No, cancelas cuando quieras." }] },
  inventory: { items: [] },
};
