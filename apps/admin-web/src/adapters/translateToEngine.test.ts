import { RESPONSE_LENGTH_MAX_WORDS } from "../contracts/businessConfig.v1";
import {
  createEmptyConfig,
  createFaq,
  createOffering,
  createPromotion,
  createRecommendationRule,
  createTransferMethod,
} from "../domain/config/factories";
import type { AssistantConfig } from "../domain/config/types";
import { SAMPLE_CONFIG } from "../test/fixtures/sampleConfig";
import { toBusinessConfig } from "./contractAdapter";
import { collectEngineNotices, type EngineNoticeCode } from "./engineNotices";
import { translateToEngine } from "./translateToEngine";

const clone = (config: AssistantConfig): AssistantConfig => structuredClone(config);
const codes = (config: AssistantConfig): EngineNoticeCode[] => collectEngineNotices(config).map((notice) => notice.code);
const translate = (config: AssistantConfig) => toBusinessConfig(config, "cafe_aroma");

function catalogWith(categories: string[]): AssistantConfig {
  const config = clone(SAMPLE_CONFIG);
  config.offerings = categories.map((category, index) => createOffering({ id: `p${index}`, name: `Producto ${index}`, category, price: 1000 }));
  return config;
}

describe("translateToEngine", () => {
  it("traduce una configuración válida al contrato global", () => {
    const result = translateToEngine(SAMPLE_CONFIG, "cafe_aroma");
    expect(result.status).toBe("ok");
    if (result.status !== "ok") return;
    expect(result.document.schema_version).toBe("1.0");
    expect(result.document.tenant_slug).toBe("cafe_aroma");
    expect(result.document.identity).toEqual({
      name: "Café Aroma",
      brand_name: null,
      industry: "cafetería con domicilios",
      description: "Cafetería de barrio que vende café, panadería y desayunos para llevar.",
      value_proposition: "Tu desayuno listo en minutos, pedido directo por chat y sin filas.",
      differentiators: ["Pan horneado cada mañana"],
      location: { type: "fisico", address: "Calle 10 #20-30", city: "Ciudad Ejemplo", coverage: { type: "local", zones: ["Centro"] } },
      service_modes: ["domicilio", "recoger"],
    });
    expect(result.document.engine).toBeUndefined();
  });

  it("produce el documento que valida el contrato de Python (tests/test_business_config_contract.py)", async () => {
    // El mismo archivo lo valida el modelo canónico de Python: si el adaptador cambia, ambas pruebas lo detectan.
    const document = `${JSON.stringify(translate(SAMPLE_CONFIG).document, null, 2)}\n`;
    await expect(document).toMatchFileSnapshot("../test/fixtures/sampleContractDocument.json");
  });

  it("no traduce una configuración con errores, salvo que se pida explícitamente", () => {
    const result = translateToEngine(createEmptyConfig(), "cafe_aroma");
    expect(result.status).toBe("invalid_config");
    if (result.status === "invalid_config") {
      expect(result.errors.map((issue) => issue.field)).toEqual(expect.arrayContaining(["business.name", "business.description"]));
    }
    expect(translateToEngine(createEmptyConfig(), "cafe_aroma", { allowInvalid: true }).status).toBe("ok");
  });

  it("es determinista: la misma configuración produce exactamente el mismo resultado", () => {
    expect(JSON.stringify(translate(SAMPLE_CONFIG))).toBe(JSON.stringify(translate(clone(SAMPLE_CONFIG))));
  });
});

describe("contrato: oferta, precios y pagos", () => {
  it("envía el catálogo con categorías, precios, características y disponibilidad, sin perder lo no disponible", () => {
    const { document } = translate(SAMPLE_CONFIG);
    expect(document.offer.model).toBe("catalog");
    expect(document.offer.catalog?.categories).toEqual([
      { id: "bebidas", name: "Bebidas" },
      { id: "panaderia", name: "Panadería" },
      { id: "desayunos", name: "Desayunos" },
    ]);
    expect(document.offer.catalog?.items.map((item) => [item.name, item.prices, item.features, item.available])).toEqual([
      ["Café americano", [{ currency: "COP", amount: 6000 }], ["Tamaño 12 oz"], true],
      ["Croissant de mantequilla", [{ currency: "COP", amount: 5500 }], null, true],
      ["Desayuno completo", [{ currency: "COP", amount: 18000 }], ["Incluye bebida caliente"], false],
    ]);
  });

  it("envía los planes con cobro mensual, costo inicial, inclusiones y exclusiones", () => {
    const config = clone(SAMPLE_CONFIG);
    config.business.salesMode = "plans";
    config.offerings = [
      createOffering({ id: "pro", name: "Plan Pro", price: 90000, setupFee: 150000, billing: "monthly", features: ["Soporte"], notIncluded: ["Hardware"] }),
      createOffering({ id: "unico", name: "Asesoría", price: 50000, billing: "one_time", currency: "USD" }),
    ];
    expect(translate(config).document.offer.plans).toEqual([
      { id: "pro", name: "Plan Pro", description: null, prices: [{ currency: "COP", implementation: 150000, monthly: 90000 }], includes: ["Soporte"], not_included: ["Hardware"], payment_profile: "principal", available: true },
      { id: "unico", name: "Asesoría", description: null, prices: [{ currency: "USD", price: 50000 }], includes: [], not_included: [], payment_profile: "principal", available: true },
    ]);
  });

  it("nunca incluye datos de pago en el documento: los devuelve aparte como secretos", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.transferMethods.push(
      createTransferMethod({ type: "bank", bankName: "Banco Ejemplo", accountType: "corriente", accountNumber: "123-456-789" }),
      createTransferMethod({ type: "breb", reference: "@cafe-aroma" }),
    );
    const { document, secrets } = translate(config);
    const serialized = JSON.stringify(document);
    for (const value of ["pagos.example.com", "3000000000", "123456789", "@cafe-aroma"]) expect(serialized).not.toContain(value);
    expect(Object.values(secrets)).toEqual(["https://pagos.example.com/cafe-aroma", "3000000000", "123456789", "@cafe-aroma"]);
    const profile = document.payments?.[0];
    expect(profile?.link?.secret_ref).toBe("secret_store:principal.link");
    expect(profile?.transfer_methods?.map((method) => method.type)).toEqual(["nequi", "bank", "breb"]);
    expect(profile?.transfer_methods?.[1]).toMatchObject({ bank: "Banco Ejemplo", account_type: "corriente" });
  });

  it("no envía medios de pago desactivados", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.paymentLinkEnabled = false;
    config.payments.transferEnabled = false;
    const { document, secrets } = translate(config);
    expect(document.payments?.[0]).toEqual({ id: "principal", link: null, transfer_enabled: false, transfer_methods: [] });
    expect(secrets).toEqual({});
  });
});

describe("contrato: comportamiento del asistente", () => {
  it.each(["short", "medium", "long"] as const)("envía la longitud de respuesta «%s»; el motor fija el límite", (length) => {
    const config = clone(SAMPLE_CONFIG);
    config.behavior.responseLength = length;
    expect(translate(config).document.response_style).toEqual({ tone: "cercano y amable", length, max_words: null });
    expect(RESPONSE_LENGTH_MAX_WORDS[length]).toBeGreaterThanOrEqual(20);
  });

  it("envía el límite avanzado de palabras y omite el tono vacío", () => {
    const config = clone(SAMPLE_CONFIG);
    config.behavior.tone = "  ";
    config.behavior.responseLength = "long";
    config.behavior.maxWords = 150;
    expect(translate(config).document.response_style).toEqual({ tone: null, length: "long", max_words: 150 });
  });

  it("envía las preguntas frecuentes completas y descarta las vacías", () => {
    const config = clone(SAMPLE_CONFIG);
    config.behavior.faqs = [
      createFaq({ question: " ¿Hacen domicilios? ", answer: " Sí, en el barrio. " }),
      createFaq({ question: "", answer: "" }),
    ];
    expect(translate(config).document.knowledge).toEqual({ faqs: [{ question: "¿Hacen domicilios?", answer: "Sí, en el barrio." }] });
  });

  it("traduce motivaciones, problemas, estrategia, cierre, canales y mensajes", () => {
    const { document } = translate(SAMPLE_CONFIG);
    expect(document.sales).toEqual({
      buying_motivation: { primary: "ahorrar tiempo en la mañana", secondary: "comer bien sin salir" },
      customer_problems: [{ id: "problema_1", impacts: ["no tienen tiempo de desayunar antes del trabajo"] }],
      benefits: ["Desayunar sin hacer fila"],
      arguments: ["Todo se prepara al momento."],
      discovery: { questions: ["¿Para cuántas personas es el pedido?"] },
      recommendation_rules: [{ when: "pide café", recommend: "sample_croissant" }],
      instructions: ["Confirma la dirección antes de cerrar el pedido."],
    });
    expect(document.capabilities).toEqual({
      service_channels: ["whatsapp"],
      product_channels: [],
      actions_primary: ["tomar_pedido", "cerrar_venta"],
      actions_support: ["responder_dudas", "confirmar_datos"],
      closing_methods: { payment_link: true, human_handoff: false, data_collection: true },
      data_collection: { enabled: true, fields: ["nombre", "telefono", "direccion"] },
    });
    expect(document.messages.welcome).toEqual({ enabled: true, text: "¡Hola! Bienvenido a Café Aroma. ¿Quieres hacer un pedido?" });
    expect(document.messages.payment_reported).toBe("Gracias, ya reviso tu pago y te confirmo en un momento.");
  });

  it("envía las recomendaciones completas aunque apunten a algo no disponible y descarta las incompletas", () => {
    const config = clone(SAMPLE_CONFIG);
    config.behavior.recommendationRules = [
      createRecommendationRule({ when: "quiere desayunar", offeringId: "sample_desayuno" }),
      createRecommendationRule({ when: "  ", offeringId: "sample_croissant" }),
      createRecommendationRule({ when: "pide algo inexistente", offeringId: "no_existe" }),
    ];
    // El motor no recomienda lo que no está disponible; el contrato lo conserva para cuando vuelva a estarlo.
    expect(translate(config).document.sales?.recommendation_rules).toEqual([{ when: "quiere desayunar", recommend: "sample_desayuno" }]);
    expect(codes(config).filter((code) => code === "recommendation_omitted")).toHaveLength(2);
  });

  it("traduce la ubicación: sin ubicación, solo virtual (sin dirección) o con local", () => {
    const config = clone(SAMPLE_CONFIG);
    config.business.location = { ...config.business.location, type: "" };
    expect(translate(config).document.identity.location).toBeNull();
    config.business.location = { ...config.business.location, type: "virtual", address: "Calle 1", coverageType: "nacional", coverageZones: [" Colombia ", ""] };
    expect(translate(config).document.identity.location).toEqual({
      type: "virtual",
      address: null,
      city: "Ciudad Ejemplo",
      coverage: { type: "nacional", zones: ["Colombia"] },
    });
  });

  it("envía las promociones completas con su vigencia y descarta las incompletas", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.promotions = [
      createPromotion({ name: " 2x1 ", details: " Dos cafés por uno ", validUntil: "2030-01-31" }),
      createPromotion({ name: "Sin detalle", details: "" }),
    ];
    expect(translate(config).document.terms?.promotions).toEqual([{ name: "2x1", details: "Dos cafés por uno", valid_until: "2030-01-31" }]);
    expect(codes(config)).toContain("promotion_omitted");
    config.payments.promotions = [];
    expect(translate(config).document.terms?.promotions).toBeNull();
  });

  it("omite los mensajes de pago vacíos en lugar de enviar texto vacío", () => {
    const config = clone(SAMPLE_CONFIG);
    config.messages.paymentReportedText = "  ";
    config.messages.paymentConfirmedText = "";
    expect(translate(config).document.messages).toMatchObject({ payment_reported: null, payment_confirmed: null });
  });
});

describe("avisos de la traducción", () => {
  it("la configuración de ejemplo no genera avisos: todo lo que tiene se envía", () => {
    expect(codes(SAMPLE_CONFIG)).toEqual([]);
  });

  it("avisa de una promoción vencida", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.promotions = [createPromotion({ name: "Antigua", details: "Ya pasó", validUntil: "2000-01-01" })];
    expect(codes(config)).toContain("promotion_expired");
  });

  it("avisa cuando dos categorías se fusionan y conserva el primer nombre", () => {
    const config = catalogWith(["Café", "cafe", "Bebidas"]);
    expect(codes(config)).toContain("categories_merged");
    const catalog = translate(config).document.offer.catalog;
    expect(catalog?.categories).toEqual([
      { id: "cafe", name: "Café" },
      { id: "bebidas", name: "Bebidas" },
    ]);
    expect(catalog?.items.map((item) => item.category)).toEqual(["cafe", "cafe", "bebidas"]);
  });

  it("agrupa en «General» los productos sin categoría y lo avisa", () => {
    const config = catalogWith(["  ", "Bebidas"]);
    expect(codes(config)).toContain("category_defaulted");
    expect(translate(config).document.offer.catalog?.categories.map((category) => category.id)).toEqual(["general", "bebidas"]);
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
    expect(translate(config).document.offer.plans?.[0]?.prices).toEqual([{ currency: "COP" }]);
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
    expect(translate(config).document.capabilities.actions_support).toContain("inventada");
  });
});
