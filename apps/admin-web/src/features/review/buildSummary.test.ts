import { SAMPLE_DOCUMENT, SAMPLE_PLANS_DOCUMENT } from "../../test/fixtures/sampleDocument";
import { buildSummary } from "./buildSummary";

const row = (document: typeof SAMPLE_DOCUMENT, section: string, label: string) =>
  buildSummary(document)
    .find((item) => item.id === section)
    ?.rows.find((item) => item.label === label)?.value;

describe("buildSummary", () => {
  it("resume todas las secciones", () => {
    expect(buildSummary(SAMPLE_DOCUMENT).map((section) => section.id)).toEqual(["business", "catalog", "payments", "assistant", "messages"]);
  });

  it("nunca incluye referencias de pago: solo indica lo configurado", () => {
    const summary = JSON.stringify(buildSummary(SAMPLE_DOCUMENT));
    expect(summary).not.toContain("secret_store");
    expect(row(SAMPLE_DOCUMENT, "payments", "Medios de pago")).toBe("2 configurados, guardados de forma segura");
    expect(row(SAMPLE_DOCUMENT, "payments", "Enlace de pago")).toBe("Configurado");
    expect(row(SAMPLE_DOCUMENT, "payments", "Transferencias")).toBe("Nequi");
  });

  it("habla en singular cuando hay un solo medio de pago y dice si no hay ninguno", () => {
    const one = structuredClone(SAMPLE_DOCUMENT);
    one.payments[0]!.link = null;
    expect(row(one, "payments", "Medios de pago")).toBe("1 configurado, guardado de forma segura");
    expect(row(SAMPLE_PLANS_DOCUMENT, "payments", "Medios de pago")).toBe("Ninguno");
    expect(row(SAMPLE_PLANS_DOCUMENT, "payments", "Enlace de pago")).toBe("Desactivado");
    expect(row(SAMPLE_PLANS_DOCUMENT, "payments", "Transferencias")).toBe("Desactivadas");
  });

  it("lista solo lo disponible, con su precio y categoría", () => {
    expect(row(SAMPLE_DOCUMENT, "catalog", "Disponibles")).toBe("2 de 3");
    expect(row(SAMPLE_DOCUMENT, "catalog", "Café americano")).toMatch(/6\.000.*Bebidas/);
    expect(row(SAMPLE_DOCUMENT, "catalog", "Desayuno completo")).toBeUndefined();
    expect(row(SAMPLE_PLANS_DOCUMENT, "catalog", "Básico")).toMatch(/50\.000.*\/ mes/);
  });

  it("indica lo que falta en vez de dejarlo en blanco", () => {
    expect(row(SAMPLE_PLANS_DOCUMENT, "assistant", "Tono")).toBe("Sin definir");
    expect(row(SAMPLE_PLANS_DOCUMENT, "assistant", "Instrucciones")).toBe("Sin definir");
    expect(row(SAMPLE_PLANS_DOCUMENT, "messages", "Bienvenida")).toBe("Desactivada");
  });
});
