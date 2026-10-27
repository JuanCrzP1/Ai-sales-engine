import { createEmptyConfig, createOffering, createTransferMethod } from "../domain/config/factories";
import type { AssistantConfig } from "../domain/config/types";
import { SAMPLE_CONFIG } from "../test/fixtures/sampleConfig";
import { checkEngineContract } from "./engineContract";
import { collectEngineNotices, type EngineNoticeCode } from "./engineNotices";
import { toEngineSections } from "./engineRuntimeAdapter";
import { translateToEngine } from "./translateToEngine";

const clone = (config: AssistantConfig): AssistantConfig => structuredClone(config);
const codes = (config: AssistantConfig): EngineNoticeCode[] => collectEngineNotices(config).map((notice) => notice.code);

function catalogWith(categories: string[]): AssistantConfig {
  const config = clone(SAMPLE_CONFIG);
  config.offerings = categories.map((category, index) => createOffering({ id: `p${index}`, name: `Producto ${index}`, category, price: 1000 }));
  return config;
}

describe("translateToEngine", () => {
  it("traduce una configuración válida y cumple el contrato mínimo", () => {
    const result = translateToEngine(SAMPLE_CONFIG);
    expect(result.status).toBe("ok");
    if (result.status === "ok") expect(checkEngineContract(result.sections)).toEqual([]);
  });

  it("no traduce una configuración con errores, salvo que se pida explícitamente", () => {
    const result = translateToEngine(createEmptyConfig());
    expect(result.status).toBe("invalid_config");
    if (result.status === "invalid_config") expect(result.errors.map((issue) => issue.field)).toContain("business.name");

    const forced = translateToEngine(createEmptyConfig(), { allowInvalid: true });
    expect(forced.status).toBe("ok");
  });

  it("es determinista: la misma configuración produce exactamente el mismo resultado", () => {
    expect(JSON.stringify(translateToEngine(SAMPLE_CONFIG))).toBe(JSON.stringify(translateToEngine(clone(SAMPLE_CONFIG))));
  });

  it("traduce listas vacías sin inventar datos", () => {
    const config = clone(SAMPLE_CONFIG);
    config.behavior = { ...config.behavior, customerProblems: [], salesRules: [], discoveryQuestions: [], recommendationNotes: "" };
    config.payments.conditions = [];
    const { sales, pricing } = toEngineSections(config);
    expect(sales).toEqual({ pain: { clusters: {} }, discovery: { questions: [] }, closing: { hard_rules: [] }, offer: { recommendation_rules: [] } });
    expect(pricing.conditions).toEqual([]);
  });
});

describe("checkEngineContract", () => {
  it("detecta las incompatibilidades con el contrato mínimo conocido", () => {
    const sections = toEngineSections(SAMPLE_CONFIG);
    const broken = { ...sections, inventory: {} as never, pricing: { conditions: [] } };
    const violations = checkEngineContract(broken);
    expect(violations).toEqual(
      expect.arrayContaining([expect.stringContaining('"inventory"'), expect.stringContaining('"plans" o "catalog"')]),
    );
  });
});

describe("avisos de la traducción", () => {
  it("la configuración de ejemplo solo avisa de lo que de verdad pasa", () => {
    expect(new Set(codes(SAMPLE_CONFIG))).toEqual(
      new Set<EngineNoticeCode>(["offering_unavailable_omitted", "catalog_field_dropped", "field_not_consumed"]),
    );
  });

  it("avisa cuando dos categorías se fusionan y conserva el primer nombre", () => {
    const config = catalogWith(["Café", "cafe", "Bebidas"]);
    expect(codes(config)).toContain("categories_merged");
    const catalog = toEngineSections(config).pricing.catalog;
    expect(catalog?.categories).toEqual([
      { id: "cafe", name: "Café" },
      { id: "bebidas", name: "Bebidas" },
    ]);
    expect(catalog?.items.map((item) => item.category)).toEqual(["cafe", "cafe", "bebidas"]);
  });

  it("agrupa en «General» los productos sin categoría y lo avisa", () => {
    const config = catalogWith(["  ", "Bebidas"]);
    expect(codes(config)).toContain("category_defaulted");
    expect(toEngineSections(config).pricing.catalog?.categories.map((category) => category.id)).toEqual(["general", "bebidas"]);
  });

  it("avisa cuando hay más categorías de las que menciona el motor", () => {
    expect(codes(catalogWith(["A", "B", "C", "D"]))).not.toContain("categories_beyond_limit");
    expect(codes(catalogWith(["A", "B", "C", "D", "E"]))).toContain("categories_beyond_limit");
  });

  it("avisa de los datos que el catálogo no envía y de la categoría que los planes no envían", () => {
    const catalog = clone(SAMPLE_CONFIG);
    catalog.offerings = [createOffering({ id: "x", name: "X", category: "A", price: 1, setupFee: 5, billing: "monthly", notIncluded: ["Y"] })];
    const notice = collectEngineNotices(catalog).find((item) => item.code === "catalog_field_dropped");
    expect(notice?.message).toMatch(/lo que no incluye.*costo inicial.*cobro mensual/);

    const plans = clone(catalog);
    plans.business.salesMode = "plans";
    expect(codes(plans)).toContain("plan_category_dropped");
  });

  it("avisa de precios ausentes cuando se traduce una configuración inválida", () => {
    const config = clone(SAMPLE_CONFIG);
    config.business.salesMode = "plans";
    config.offerings = [createOffering({ id: "sin", name: "Sin precio", price: null })];
    expect(codes(config)).toContain("price_missing");
    expect(toEngineSections(config).pricing.plans?.[0]?.pricing).toEqual({ COP: {} });
  });

  it("avisa de los medios de pago desactivados que no se envían y de cuentas repetidas", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.paymentLinkEnabled = false;
    config.payments.transferEnabled = false;
    expect(codes(config)).toEqual(expect.arrayContaining(["payment_link_disabled_dropped", "transfer_methods_disabled_dropped"]));

    const duplicated = clone(SAMPLE_CONFIG);
    duplicated.payments.transferMethods.push(createTransferMethod({ type: "nequi", phoneNumber: "3111111111" }));
    expect(codes(duplicated)).toContain("transfer_type_duplicated");
  });

  it("avisa de acciones desconocidas, problemas de más y atención humana sin aviso al equipo", () => {
    const config = clone(SAMPLE_CONFIG);
    config.closing.actions = [...config.closing.actions, "inventada"];
    config.closing.humanHandoff = true;
    config.behavior.customerProblems = ["uno", "dos", "tres"];
    expect(codes(config)).toEqual(expect.arrayContaining(["unknown_action", "human_handoff_not_notified", "problems_beyond_limit"]));
    expect(toEngineSections(config).config.capabilities.actions.support).toContain("inventada");
  });

  it("señala los datos que se envían pero el motor actual no usa", () => {
    const fields = collectEngineNotices(SAMPLE_CONFIG)
      .filter((notice) => notice.code === "field_not_consumed")
      .map((notice) => notice.field);
    expect(fields).toEqual(expect.arrayContaining(["business.name", "behavior.tone", "offering.name", "offering.price"]));
  });
});
