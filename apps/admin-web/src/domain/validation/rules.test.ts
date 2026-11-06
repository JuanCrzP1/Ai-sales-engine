import type { TransferMethod } from "../../contracts/businessConfig.v1";
import { SAMPLE_DOCUMENT } from "../../test/fixtures/sampleDocument";
import { MAX_PROFILE_ITEM_CHARS, MAX_PROFILE_ITEMS } from "../config/engineLimits";
import { createCatalogItem, createEmptyDocument, createPlan } from "../config/factories";
import type { BusinessDocument, PaymentValues } from "../config/types";
import { computeProgress } from "./progress";
import { validateDocument, validateEntry, validatePaymentValues } from "./rules";

const clone = (document: BusinessDocument): BusinessDocument => structuredClone(document);
const check = (document: BusinessDocument, paymentValues: PaymentValues = {}) => validateDocument({ document, paymentValues }, new Date(2026, 5, 15));
const errorFields = (document: BusinessDocument, paymentValues?: PaymentValues) => check(document, paymentValues).filter((issue) => issue.severity === "error").map((issue) => issue.field);
const warningFields = (document: BusinessDocument, paymentValues?: PaymentValues) => check(document, paymentValues).filter((issue) => issue.severity === "warning").map((issue) => issue.field);
const ref = (name: string) => ({ secret_ref: `secret_store:${name}` });

describe("validateDocument", () => {
  it("acepta el documento de ejemplo sin errores", () => {
    expect(errorFields(SAMPLE_DOCUMENT)).toEqual([]);
    expect(computeProgress(check(SAMPLE_DOCUMENT)).ready).toBe(true);
  });

  it("marca como pendientes los datos obligatorios de un negocio nuevo", () => {
    const empty = createEmptyDocument("nuevo", "");
    expect(errorFields(empty)).toEqual(expect.arrayContaining(["identity.name", "identity.industry", "identity.description", "identity.value_proposition", "offer"]));
    expect(computeProgress(check(empty)).ready).toBe(false);
  });

  it("avisa cuando los textos superan el límite de palabras que usa el motor", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.identity.industry = "uno dos tres cuatro cinco seis siete ocho nueve";
    document.identity.value_proposition = Array.from({ length: 31 }, (_, i) => `p${i}`).join(" ");
    expect(warningFields(document)).toEqual(expect.arrayContaining(["identity.industry", "identity.value_proposition"]));
  });

  it("exige precio y categoría válidos en cada elemento del catálogo", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.offer.catalog!.items = [createCatalogItem({ id: "x", name: "Galleta", category: "", prices: [{ currency: "COP", amount: 0 }] })];
    expect(errorFields(document)).toEqual(expect.arrayContaining(["offer.catalog.items.0.prices", "offer.catalog.items.0.category"]));
  });

  it("avisa cuando hay más categorías de las que menciona el motor", () => {
    const document = clone(SAMPLE_DOCUMENT);
    const named = (ids: string[]) => ids.map((id) => ({ id, name: id }));
    document.offer.catalog!.categories = named(["a", "b", "c", "d"]);
    expect(warningFields(document)).not.toContain("offer.catalog.categories");
    document.offer.catalog!.categories = named(["a", "b", "c", "d", "e"]);
    expect(warningFields(document)).toContain("offer.catalog.categories");
  });

  it("exige al menos un elemento disponible", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.offer.catalog!.items = document.offer.catalog!.items.map((item) => ({ ...item, available: false }));
    expect(errorFields(document)).toContain("offer");
  });

  it("no exige categoría cuando se venden planes, pero sí un precio", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.offer = { model: "plans", plans: [createPlan({ id: "p", name: "Plan", prices: [{ currency: "COP", monthly: 100 }] }), createPlan({ id: "q", name: "Sin precio" })] };
    const errors = errorFields(document);
    expect(errors).not.toContain("offer.plans.0.category");
    expect(errors).not.toContain("offer.plans.0.prices");
    expect(errors).toContain("offer.plans.1.prices");
  });

  it("no admite dos precios en la misma moneda", () => {
    const issues = validateEntry(createPlan({ name: "Plan", prices: [{ currency: "COP", monthly: 1 }, { currency: "COP", annual: 2 }] }), false);
    expect(issues.map((issue) => issue.message)).toContain("Plan: hay dos precios en la misma moneda.");
  });

  it("en el formulario de edición valida la categoría por el nombre escrito", () => {
    const item = createCatalogItem({ name: "Té", prices: [{ currency: "COP", amount: 1000 }] });
    expect(validateEntry(item, true, "").map((issue) => issue.field)).toContain("category");
    expect(validateEntry(item, true, "Bebidas").map((issue) => issue.field)).not.toContain("category");
  });

  it("valida el formato de los datos de pago nuevos sin mirar los guardados", () => {
    const document = clone(SAMPLE_DOCUMENT);
    const [profile] = document.payments;
    expect(errorFields(document)).not.toContain("payments.0.link");
    expect(errorFields(document, { [profile!.link!.secret_ref]: "no-es-un-enlace" })).toContain("payments.0.link");
    expect(errorFields(document, { [profile!.link!.secret_ref]: "" })).toContain("payments.0.link");
    expect(warningFields(document, { [profile!.link!.secret_ref]: "http://pagos.example.com" })).toContain("payments.0.link");
    expect(errorFields(document, { [profile!.link!.secret_ref]: "https://pagos.example.com" })).not.toContain("payments.0.link");
  });

  it("valida cada tipo de cuenta de transferencia", () => {
    const document = clone(SAMPLE_DOCUMENT);
    const methods: TransferMethod[] = [
      { type: "nequi", number: ref("n") },
      { type: "bank", bank: "", account_type: "ahorros", account_number: ref("b") },
      { type: "breb", reference: ref("r") },
    ];
    document.payments[0]!.transfer_methods = methods;
    const values = { "secret_store:n": "123", "secret_store:b": "abc", "secret_store:r": " " };
    expect(errorFields(document, values)).toEqual(
      expect.arrayContaining([
        "payments.0.transfer_methods.0.number",
        "payments.0.transfer_methods.1.bank",
        "payments.0.transfer_methods.1.account_number",
        "payments.0.transfer_methods.2.reference",
      ]),
    );
    expect(errorFields(document, { "secret_store:n": "3001234567", "secret_store:b": "1234567", "secret_store:r": "llave" })).not.toContain("payments.0.transfer_methods.0.number");
  });

  it("solo devuelve los formatos de pago que bloquean el guardado", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.payments[0]!.transfer_methods = [{ type: "nequi", number: ref("n") }];
    expect(validatePaymentValues({ document, paymentValues: {} })).toEqual([]);
    expect(validatePaymentValues({ document, paymentValues: { "secret_store:n": "123" } }).map((issue) => issue.field)).toEqual(["payments.0.transfer_methods.0.number"]);
  });

  it("un reemplazo vacío de un dato guardado no es un error; uno vacío de un dato nuevo, sí", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.payments[0]!.transfer_methods = [{ type: "nequi", number: ref("guardado~v1") }, { type: "daviplata", number: ref("nuevo") }];
    const paymentValues = { "secret_store:guardado~v1": "  ", "secret_store:nuevo": "" };
    expect(validatePaymentValues({ document, paymentValues }).map((issue) => issue.field)).toEqual(["payments.0.transfer_methods.1.number"]);
  });

  it("exige al menos una cuenta cuando las transferencias están activas", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.payments[0]!.transfer_methods = [];
    expect(errorFields(document)).toContain("payments.0.transfer_methods");
  });

  it("los métodos inactivos no cuentan como medio de pago", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.payments[0]!.link_enabled = false;
    document.payments[0]!.transfer_methods = [{ type: "nequi", number: ref("a"), enabled: false }];
    expect(errorFields(document)).not.toContain("payments.0.transfer_methods");
    expect(warningFields(document)).toEqual(expect.arrayContaining(["payments", "payments.0.transfer_methods", "capabilities.closing_methods.payment_link"]));
  });

  it("una cuenta inactiva repetida no provoca el aviso de duplicados", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.payments[0]!.transfer_methods = [
      { type: "nequi", number: ref("a") },
      { type: "nequi", number: ref("b"), enabled: false },
    ];
    expect(warningFields(document)).not.toContain("payments.0.transfer_methods.duplicates");
  });

  it("avisa de cuentas repetidas por tipo, porque el motor solo usa la primera", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.payments[0]!.transfer_methods = [
      { type: "nequi", number: ref("a") },
      { type: "nequi", number: ref("b") },
    ];
    expect(warningFields(document)).toContain("payments.0.transfer_methods.duplicates");
  });

  it("avisa cuando no hay ningún medio de pago", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.payments = [];
    expect(warningFields(document)).toEqual(expect.arrayContaining(["payments", "capabilities.closing_methods.payment_link"]));
  });

  it("exige al menos una forma de cierre y una acción", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.capabilities = {
      ...document.capabilities,
      closing_methods: { payment_link: false, human_handoff: false, data_collection: false },
      data_collection: { enabled: false, fields: [] },
      actions_primary: [],
      actions_support: [],
    };
    expect(errorFields(document)).toEqual(expect.arrayContaining(["capabilities.closing_methods", "capabilities.actions"]));
  });

  it("exige elegir qué datos pedir si se piden datos", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.capabilities.data_collection = { enabled: true, fields: [] };
    expect(errorFields(document)).toContain("capabilities.data_collection");
  });

  it("advierte que la atención humana todavía no notifica a nadie", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.capabilities.closing_methods.human_handoff = true;
    expect(warningFields(document)).toContain("capabilities.closing_methods.human_handoff");
  });

  it("exige texto cuando la bienvenida está activada", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.messages.welcome.text = "  ";
    expect(errorFields(document)).toContain("messages.welcome.text");
  });

  it("revisa promociones: completas y sin vencer", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.terms.promotions = [
      { name: "", details: "" },
      { name: "Vieja", details: "Ya pasó", valid_until: "2026-06-14" },
      { name: "Vigente", details: "Todavía sirve", valid_until: "2026-06-15" },
    ];
    expect(errorFields(document)).toEqual(expect.arrayContaining(["terms.promotions.0.name", "terms.promotions.0.details"]));
    expect(warningFields(document)).toContain("terms.promotions.1.valid_until");
    expect(warningFields(document)).not.toContain("terms.promotions.2.valid_until");
  });

  it("revisa preguntas frecuentes: pregunta y respuesta", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.knowledge.faqs = [{ question: "", answer: "" }];
    expect(errorFields(document)).toEqual(expect.arrayContaining(["knowledge.faqs.0.question", "knowledge.faqs.0.answer"]));
  });

  it("revisa recomendaciones: situación, destino y disponibilidad", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.sales.recommendation_rules = [
      { when: "", recommend: "" },
      { when: "pide desayuno", recommend: "sample_desayuno" },
    ];
    expect(errorFields(document)).toEqual(expect.arrayContaining(["sales.recommendation_rules.0.when", "sales.recommendation_rules.0.recommend"]));
    expect(warningFields(document)).toContain("sales.recommendation_rules.1.recommend");
  });

  it("comprueba el límite de palabras contra el rango del largo elegido", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.response_style = { length: "short", max_words: 2 };
    expect(errorFields(document)).toContain("response_style.max_words");
    document.response_style = { length: "short", max_words: null };
    expect(errorFields(document)).not.toContain("response_style.max_words");
  });

  it("limita el largo de las listas comerciales como el contrato", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.sales.benefits = Array.from({ length: MAX_PROFILE_ITEMS + 1 }, (_, index) => `Beneficio ${index}`);
    document.sales.arguments = ["x".repeat(MAX_PROFILE_ITEM_CHARS + 1)];
    expect(errorFields(document)).toEqual(expect.arrayContaining(["sales.benefits", "sales.arguments"]));
  });

  it("avisa si el asistente no sabe por qué le compran al negocio", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.sales = {};
    expect(warningFields(document)).toContain("sales.customer_problems");
  });

  it("sin dirección avisa solo cuando hay local físico", () => {
    const document = clone(SAMPLE_DOCUMENT);
    document.identity.location = { type: "fisico", address: "" };
    expect(warningFields(document)).toContain("identity.location.address");
    document.identity.location = { type: "virtual" };
    expect(warningFields(document)).not.toContain("identity.location.address");
  });
});
