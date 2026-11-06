import { SAMPLE_CONFIG } from "../../test/fixtures/sampleConfig";
import { createEmptyConfig, createOffering, createTransferMethod } from "../config/factories";
import type { AssistantConfig } from "../config/types";
import { computeProgress } from "./progress";
import { validateConfig } from "./rules";

const clone = (config: AssistantConfig): AssistantConfig => structuredClone(config);
const errorFields = (config: AssistantConfig) =>
  validateConfig(config).filter((issue) => issue.severity === "error").map((issue) => issue.field);
const warningFields = (config: AssistantConfig) =>
  validateConfig(config).filter((issue) => issue.severity === "warning").map((issue) => issue.field);

describe("validateConfig", () => {
  it("acepta la configuración de ejemplo sin errores", () => {
    expect(errorFields(SAMPLE_CONFIG)).toEqual([]);
    expect(computeProgress(validateConfig(SAMPLE_CONFIG)).ready).toBe(true);
  });

  it("marca como pendientes los datos obligatorios de una configuración vacía", () => {
    const errors = errorFields(createEmptyConfig());
    expect(errors).toEqual(
      expect.arrayContaining(["business.name", "business.businessType", "business.valueProposition", "offerings"]),
    );
    expect(computeProgress(validateConfig(createEmptyConfig())).ready).toBe(false);
  });

  it("avisa cuando los textos superan el límite de palabras que usa el motor", () => {
    const config = clone(SAMPLE_CONFIG);
    config.business.businessType = "uno dos tres cuatro cinco seis siete ocho nueve";
    config.business.valueProposition = Array.from({ length: 31 }, (_, i) => `p${i}`).join(" ");
    expect(warningFields(config)).toEqual(expect.arrayContaining(["business.businessType", "business.valueProposition"]));
  });

  it("exige precio y categoría válidos en cada elemento del catálogo", () => {
    const config = clone(SAMPLE_CONFIG);
    const offering = createOffering({ id: "x", name: "Galleta", price: 0, category: "" });
    config.offerings = [offering];
    expect(errorFields(config)).toEqual(expect.arrayContaining(["offerings.x.price", "offerings.x.category"]));
  });

  it("exige al menos un elemento disponible", () => {
    const config = clone(SAMPLE_CONFIG);
    config.offerings = config.offerings.map((offering) => ({ ...offering, available: false }));
    expect(errorFields(config)).toContain("offerings");
  });

  it("no exige categoría cuando se venden planes", () => {
    const config = clone(SAMPLE_CONFIG);
    config.business.salesMode = "plans";
    config.offerings = [createOffering({ id: "p", name: "Plan", price: 100, category: "" })];
    expect(errorFields(config)).not.toContain("offerings.p.category");
  });

  it("valida el enlace de pago", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.paymentLink = "no-es-un-enlace";
    expect(errorFields(config)).toContain("payments.paymentLink");
    config.payments.paymentLink = "http://pagos.example.com";
    expect(warningFields(config)).toContain("payments.paymentLink");
  });

  it("valida cada tipo de cuenta de transferencia", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.transferMethods = [
      createTransferMethod({ id: "n", type: "nequi", phoneNumber: "123" }),
      createTransferMethod({ id: "b", type: "bank", bankName: "", accountNumber: "abc" }),
      createTransferMethod({ id: "r", type: "breb", reference: " " }),
    ];
    expect(errorFields(config)).toEqual(
      expect.arrayContaining([
        "payments.transfer.n.phoneNumber",
        "payments.transfer.b.bankName",
        "payments.transfer.b.accountNumber",
        "payments.transfer.r.reference",
      ]),
    );
  });

  it("exige al menos una cuenta cuando las transferencias están activas", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.transferMethods = [];
    expect(errorFields(config)).toContain("payments.transferMethods");
  });

  it("avisa de cuentas repetidas por tipo, porque el motor solo usa la primera", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.transferMethods = [
      createTransferMethod({ type: "nequi", phoneNumber: "3001112222" }),
      createTransferMethod({ type: "nequi", phoneNumber: "3003334444" }),
    ];
    expect(warningFields(config)).toContain("payments.transferMethods.duplicates");
  });

  it("avisa cuando no hay ningún medio de pago", () => {
    const config = clone(SAMPLE_CONFIG);
    config.payments.paymentLinkEnabled = false;
    config.payments.transferEnabled = false;
    expect(warningFields(config)).toEqual(expect.arrayContaining(["payments", "closing.sendPaymentLink"]));
  });

  it("exige al menos una forma de cierre y una acción", () => {
    const config = clone(SAMPLE_CONFIG);
    config.closing = { ...config.closing, sendPaymentLink: false, humanHandoff: false, collectCustomerData: false, actions: [] };
    expect(errorFields(config)).toEqual(expect.arrayContaining(["closing.methods", "closing.actions"]));
  });

  it("advierte que la atención humana todavía no notifica a nadie", () => {
    const config = clone(SAMPLE_CONFIG);
    config.closing.humanHandoff = true;
    expect(warningFields(config)).toContain("closing.humanHandoff");
  });

  it("exige texto cuando la bienvenida está activada", () => {
    const config = clone(SAMPLE_CONFIG);
    config.messages.welcomeText = "  ";
    expect(errorFields(config)).toContain("messages.welcomeText");
  });
});
