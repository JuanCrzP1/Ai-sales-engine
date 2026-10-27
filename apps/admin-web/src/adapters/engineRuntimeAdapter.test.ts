import { SAMPLE_CONFIG } from "../test/fixtures/sampleConfig";
import { createOffering, createTransferMethod } from "../domain/config/factories";
import type { AssistantConfig } from "../domain/config/types";
import { categoryId, toEngineSections } from "./engineRuntimeAdapter";
import type { EngineTenantSections } from "./engineTypes";

const clone = (config: AssistantConfig): AssistantConfig => structuredClone(config);

/**
 * Reproduce las comprobaciones mínimas de `RuntimeYamlBuilder._validate`
 * (project/app/application/runtime/runtime_yaml_builder.py) sin ejecutar el motor.
 */
function assertEngineContract(sections: EngineTenantSections) {
  for (const key of ["sales", "business", "pricing", "inventory", "config"] as const) {
    expect(typeof sections[key]).toBe("object");
    expect(Object.keys(sections[key]).length).toBeGreaterThan(0);
  }
  expect("plans" in sections.pricing || "catalog" in sections.pricing).toBe(true);
  expect("description" in sections.business).toBe(true);
}

function plansConfig(): AssistantConfig {
  const config = clone(SAMPLE_CONFIG);
  config.business.salesMode = "plans";
  config.offerings = [
    createOffering({
      id: "basico",
      name: " Plan Básico ",
      description: "Para empezar",
      price: 120000,
      setupFee: 100000,
      billing: "monthly",
      features: ["Soporte", " "],
      notIncluded: ["Publicidad"],
    }),
    createOffering({ id: "unico", name: "Asesoría", price: 50000, billing: "one_time", currency: "USD" }),
    createOffering({ id: "pausado", name: "Pausado", price: 1, available: false }),
  ];
  return config;
}

describe("toEngineSections", () => {
  it("cumple el contrato mínimo del motor en modo catálogo y en modo planes", () => {
    assertEngineContract(toEngineSections(SAMPLE_CONFIG));
    assertEngineContract(toEngineSections(plansConfig()));
  });

  it("traduce planes con los campos de precio que lee el motor", () => {
    const { pricing, config } = toEngineSections(plansConfig());
    expect(pricing.catalog).toBeUndefined();
    expect(pricing.plans?.map((plan) => plan.id)).toEqual(["basico", "unico"]);
    expect(pricing.plans?.[0]).toMatchObject({
      name: "Plan Básico",
      pricing: { COP: { implementation: 100000, monthly: 120000 } },
      includes: ["Soporte"],
      not_included: ["Publicidad"],
    });
    expect(pricing.plans?.[1]?.pricing).toEqual({ USD: { price: 50000 } });
    expect(config.features).toEqual({ pricing_enabled: true, catalog_mode: false });
  });

  it("repite el bloque de pago en cada plan, como en los negocios existentes", () => {
    const { pricing } = toEngineSections(plansConfig());
    const [first, second] = pricing.plans ?? [];
    expect(first?.payment).toEqual(second?.payment);
    expect(first?.payment).toEqual({
      link: "https://pagos.example.com/cafe-aroma",
      transfer: { enabled: true, methods: [{ type: "nequi", number: "3000000000" }] },
    });
  });

  it("traduce el catálogo derivando categorías y excluye lo no disponible", () => {
    const { pricing, config } = toEngineSections(SAMPLE_CONFIG);
    expect(pricing.model).toBe("catalog");
    expect(pricing.catalog?.categories).toEqual([
      { id: "bebidas", name: "Bebidas" },
      { id: "panaderia", name: "Panadería" },
    ]);
    expect(pricing.catalog?.items.map((item) => item.id)).toEqual(["sample_cafe_americano", "sample_croissant"]);
    expect(pricing.catalog?.items[0]).toMatchObject({ category: "bebidas", price: { COP: 6000 } });
    expect(config.features).toEqual({ pricing_enabled: true, catalog_mode: true, business_model: "catalog" });
  });

  it("traduce cada tipo de transferencia a la forma que usa ejecutar_pago", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.transferMethods = [
      createTransferMethod({ type: "daviplata", phoneNumber: "300 111 2222" }),
      createTransferMethod({ type: "bank", bankName: "Banco Ejemplo", accountType: "corriente", accountNumber: "123-456-789" }),
      createTransferMethod({ type: "breb", reference: "llave-ejemplo" }),
    ];
    expect(toEngineSections(config).pricing.catalog?.payment.transfer.methods).toEqual([
      { type: "daviplata", number: "3001112222" },
      { type: "bank", bank: "Banco Ejemplo", account_type: "corriente", account_number: "123456789" },
      { type: "breb", reference: "llave-ejemplo" },
    ]);
  });

  it("no envía datos de pago desactivados", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.paymentLinkEnabled = false;
    config.payments.transferEnabled = false;
    expect(toEngineSections(config).pricing.catalog?.payment).toEqual({ link: "", transfer: { enabled: false, methods: [] } });
  });

  it("separa acciones de venta y de apoyo y replica los canales en el campo heredado", () => {
    const { capabilities } = toEngineSections(SAMPLE_CONFIG).config;
    expect(capabilities.actions).toEqual({
      primary: ["tomar_pedido", "cerrar_venta"],
      support: ["responder_dudas", "confirmar_datos"],
    });
    expect(capabilities.channels).toEqual(capabilities.business_channels.allowed);
    expect(capabilities.closing_methods.data_collection.enabled).toBe(capabilities.data_collection.enabled);
  });

  it("traduce mensajes, longitud de respuesta y conocimiento comercial", () => {
    const sections = toEngineSections(SAMPLE_CONFIG);
    expect(sections.config.response).toEqual({ length: "short", max_words: 60 });
    expect(sections.config.initial_message).toEqual({ enabled: true, text: SAMPLE_CONFIG.messages.welcomeText });
    expect(sections.config.post_payment.on_user_report.message).toBe(SAMPLE_CONFIG.messages.paymentReportedText);
    expect(sections.business).toMatchObject({
      industry: "cafetería con domicilios",
      promise: SAMPLE_CONFIG.business.valueProposition,
      buying_motivation: { primary: "ahorrar tiempo en la mañana", secondary: "comer bien sin salir" },
    });
    expect(sections.sales.pain.clusters).toEqual({
      problema_1: { impacts: ["no tienen tiempo de desayunar antes del trabajo"] },
    });
  });

  it("omite las motivaciones si no hay ninguna", () => {
    const config = clone(SAMPLE_CONFIG);
    config.behavior.primaryMotivation = "";
    config.behavior.secondaryMotivation = " ";
    expect(toEngineSections(config).business.buying_motivation).toBeUndefined();
  });

  it("genera identificadores de categoría estables y sin tildes", () => {
    expect(categoryId("  Panadería & Café ")).toBe("panaderia_cafe");
    expect(categoryId("")).toBe("general");
  });
});
