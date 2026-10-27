import { SAMPLE_CONFIG } from "../../test/fixtures/sampleConfig";
import { createEmptyConfig, createOffering, createTransferMethod } from "./factories";
import {
  addTransferMethod,
  changeTransferMethodType,
  removeOffering,
  removeTransferMethod,
  saveOffering,
  setOfferingAvailability,
  updateSection,
  updateTransferMethod,
} from "./operations";

// Reemplaza a las pruebas de `configReducer`: el reducer se sustituyó por estas operaciones puras.
describe("operaciones de configuración", () => {
  it("actualiza una sección sin tocar las demás ni mutar la original", () => {
    const next = updateSection(SAMPLE_CONFIG, "business", { name: "Otro" });
    expect(next.business.name).toBe("Otro");
    expect(next.business.businessType).toBe(SAMPLE_CONFIG.business.businessType);
    expect(next.payments).toBe(SAMPLE_CONFIG.payments);
    expect(SAMPLE_CONFIG.business.name).toBe("Café Aroma");
  });

  it("agrega, edita y elimina productos", () => {
    const offering = createOffering({ id: "nuevo", name: "Té" });
    const added = saveOffering(createEmptyConfig(), offering);
    expect(added.offerings).toEqual([offering]);
    const edited = saveOffering(added, { ...offering, name: "Té verde" });
    expect(edited.offerings).toEqual([{ ...offering, name: "Té verde" }]);
    expect(removeOffering(edited, "nuevo").offerings).toEqual([]);
  });

  it("pausa y activa un producto sin cambiar el resto", () => {
    const paused = setOfferingAvailability(SAMPLE_CONFIG, "sample_croissant", false);
    expect(paused.offerings.find((item) => item.id === "sample_croissant")?.available).toBe(false);
    expect(paused.offerings.find((item) => item.id === "sample_cafe_americano")).toBe(
      SAMPLE_CONFIG.offerings.find((item) => item.id === "sample_cafe_americano"),
    );
  });

  it("agrega, edita y quita cuentas de transferencia", () => {
    const method = createTransferMethod({ id: "t1" });
    const added = addTransferMethod(createEmptyConfig(), method);
    expect(added.payments.transferMethods).toEqual([method]);
    const edited = updateTransferMethod(added, "t1", { phoneNumber: "3001234567" });
    expect(edited.payments.transferMethods[0]?.phoneNumber).toBe("3001234567");
    expect(removeTransferMethod(edited, "t1").payments.transferMethods).toEqual([]);
  });

  it("al cambiar el tipo de cuenta borra los datos del tipo anterior", () => {
    const nequi = createTransferMethod({ id: "t1", type: "nequi", phoneNumber: "3001234567" });
    const config = addTransferMethod(createEmptyConfig(), nequi);

    const bank = changeTransferMethodType(config, "t1", "bank").payments.transferMethods[0];
    expect(bank).toEqual(createTransferMethod({ id: "t1", type: "bank" }));
    expect(bank?.phoneNumber).toBe("");

    const withBank = updateTransferMethod(changeTransferMethodType(config, "t1", "bank"), "t1", {
      bankName: "Banco Ejemplo",
      accountNumber: "123456789",
    });
    const breb = changeTransferMethodType(withBank, "t1", "breb").payments.transferMethods[0];
    expect(breb).toMatchObject({ type: "breb", bankName: "", accountNumber: "", reference: "" });
  });

  it("cambiar al mismo tipo no borra nada", () => {
    const nequi = createTransferMethod({ id: "t1", type: "nequi", phoneNumber: "3001234567" });
    const config = addTransferMethod(createEmptyConfig(), nequi);
    expect(changeTransferMethodType(config, "t1", "nequi").payments.transferMethods[0]).toBe(nequi);
  });
});
