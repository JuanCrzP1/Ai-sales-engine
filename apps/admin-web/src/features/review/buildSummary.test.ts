import { SAMPLE_CONFIG } from "../../test/fixtures/sampleConfig";
import { createTransferMethod } from "../../domain/config/factories";
import { buildSummary } from "./buildSummary";

describe("buildSummary", () => {
  it("resume todas las secciones", () => {
    expect(buildSummary(SAMPLE_CONFIG).map((section) => section.id)).toEqual(["business", "catalog", "payments", "assistant", "messages"]);
  });

  it("no muestra números de cuenta completos", () => {
    const config = structuredClone(SAMPLE_CONFIG);
    config.payments.transferMethods = [createTransferMethod({ type: "bank", bankName: "Banco Ejemplo", accountNumber: "9876543210" })];
    const payments = buildSummary(config).find((section) => section.id === "payments");
    const transfers = payments?.rows.find((row) => row.label === "Transferencias")?.value ?? "";
    expect(transfers).toContain("terminada en 3210");
    expect(transfers).not.toContain("9876543210");
  });
});
