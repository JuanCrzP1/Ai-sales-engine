import { SAMPLE_DOCUMENT } from "../../test/fixtures/sampleDocument";
import { paymentOptionCounts } from "./document";
import { summarizePaymentMethods } from "./paymentMethods";
import type { BusinessDocument, PaymentProfile } from "./types";

const ref = (name: string) => ({ secret_ref: `secret_store:${name}~guardado` });
const withProfiles = (...payments: PaymentProfile[]): BusinessDocument => ({ ...SAMPLE_DOCUMENT, payments });
const PROFILE: PaymentProfile = {
  id: "principal",
  link: ref("enlace"),
  transfer_enabled: true,
  transfer_methods: [
    { type: "nequi", number: ref("nequi") },
    { type: "daviplata", number: ref("daviplata"), enabled: false, label: "Caja" },
    { type: "bank", bank: "Banco Ejemplo", account_type: "corriente", account_number: ref("cuenta"), label: "Ana Pérez" },
    { type: "breb", reference: ref("llave") },
  ],
};

describe("summarizePaymentMethods", () => {
  const fields = {
    [ref("enlace").secret_ref]: { status: "configured" as const, masked: "https://pagos.example.com/••••" },
    [ref("nequi").secret_ref]: { status: "configured" as const, masked: "••••4567" },
    [ref("daviplata").secret_ref]: { status: "missing" as const, masked: null },
    [ref("cuenta").secret_ref]: { status: "unreadable" as const, masked: null },
    [ref("llave").secret_ref]: { status: "configured" as const, masked: "••••ave" },
  };

  it("permite reconocer cada método: nombre, banco, tipo de cuenta, etiqueta, estado y dato enmascarado", () => {
    expect(summarizePaymentMethods(withProfiles(PROFILE), fields, {})).toEqual([
      { path: "payments.0.link", name: "Enlace de pago", details: [], active: true, masked: "https://pagos.example.com/••••", dataState: "configured" },
      { path: "payments.0.transfer_methods.0", name: "Nequi", details: [], active: true, masked: "••••4567", dataState: "configured" },
      { path: "payments.0.transfer_methods.1", name: "Daviplata", details: ["Caja"], active: false, masked: null, dataState: "missing" },
      { path: "payments.0.transfer_methods.2", name: "Banco Ejemplo", details: ["Cuenta corriente", "Ana Pérez"], active: true, masked: null, dataState: "unreadable" },
      { path: "payments.0.transfer_methods.3", name: "Bre-B", details: [], active: true, masked: "••••ave", dataState: "configured" },
    ]);
  });

  it("señala lo que se escribió y aún no se guarda, sin mostrarlo", () => {
    const [link] = summarizePaymentMethods(withProfiles(PROFILE), fields, { [ref("enlace").secret_ref]: "https://otro.example.com" });
    expect(link).toMatchObject({ dataState: "pending", masked: null });
    expect(JSON.stringify(link)).not.toContain("otro.example.com");
  });

  it("un enlace inactivo o unas transferencias apagadas se ven como inactivos", () => {
    const [link, nequi] = summarizePaymentMethods(withProfiles({ ...PROFILE, link_enabled: false, transfer_enabled: false }), fields, {});
    expect(link?.active).toBe(false);
    expect(nequi?.active).toBe(false);
  });

  it("indica el perfil solo cuando hay varios", () => {
    const summaries = summarizePaymentMethods(withProfiles(PROFILE, { id: "otro", transfer_enabled: false }), fields, {});
    expect(summaries[0]?.details).toEqual(["Perfil principal"]);
  });

  it("cuenta por separado lo que se ofrece y lo que se conserva sin ofrecerse", () => {
    expect(paymentOptionCounts(withProfiles(PROFILE))).toEqual({ active: 4, inactive: 1 });
    expect(paymentOptionCounts(withProfiles({ ...PROFILE, link_enabled: false, transfer_enabled: false }))).toEqual({ active: 0, inactive: 5 });
    expect(paymentOptionCounts(withProfiles())).toEqual({ active: 0, inactive: 0 });
  });
});
