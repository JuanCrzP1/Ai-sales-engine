import { describe, expect, it } from "vitest";
import { waitNotice } from "../attention/types";
import { PLATFORM_FALLBACK_REPLY } from "../assistant/fallback";
import { phraseFor } from "./formality";
import { DEFAULT_PAYMENT_DETAILS, isDefaultPaymentDetails, recommendedPaymentDetails, renderPaymentDetails } from "./paymentMessage";

// Las vistas previas muestran los textos de la plataforma como le llegan al cliente: de usted solo si el negocio es formal.
describe("el trato en los textos de la plataforma", () => {
  it("solo «formal» cambia el texto", () => {
    expect(phraseFor(PLATFORM_FALLBACK_REPLY, "formal")).toContain("no puedo responderle; por favor escríbanos");
    for (const other of ["informal", "neutral", null, undefined, ""] as const) {
      expect(phraseFor(PLATFORM_FALLBACK_REPLY, other)).toBe(PLATFORM_FALLBACK_REPLY.tu);
    }
  });

  it("la plantilla de pago de la plataforma va con el trato; la del negocio, tal cual", () => {
    const values = { medio: "Nequi", datos: "3001234567" };
    expect(renderPaymentDetails(null, values, { formality: "formal" })).toMatch(/Cuando pague, envíeme aquí la captura del comprobante y le confirmamos\. ✅$/);
    expect(renderPaymentDetails(null, values, { formality: "informal" })).toMatch(/Cuando pagues, envíame aquí la captura del comprobante y te confirmamos\. ✅$/);
    expect(renderPaymentDetails("Datos: {datos}. Cuando pagues, avísame.", values, { formality: "formal", emojis: false })).toBe("Datos: 3001234567. Cuando pagues, avísame.");
    // Las dos plantillas de la plataforma no se guardan como propias: así siguen el trato si el negocio lo cambia.
    expect(isDefaultPaymentDetails(DEFAULT_PAYMENT_DETAILS.tu) && isDefaultPaymentDetails(`${DEFAULT_PAYMENT_DETAILS.usted}\n`)).toBe(true);
    expect(isDefaultPaymentDetails("Datos: {datos}")).toBe(false);
  });

  it("sin emojis si el negocio no los quiere, y su plantilla propia no se toca", () => {
    const values = { medio: "Nequi", datos: "3001234567" };
    expect(renderPaymentDetails(null, values, { formality: "formal", emojis: false })).toBe(
      "*Datos para pagar*\n\n*Nequi*\n3001234567\n\nCuando pague, envíeme aquí la captura del comprobante y le confirmamos.",
    );
    for (const emojis of [true, null, undefined]) expect(renderPaymentDetails(null, values, { emojis })).toMatch(/^💳 [^]*✅$/);
    expect(renderPaymentDetails("🎉 {datos}", values, { emojis: false })).toBe("🎉 3001234567");
    // La recomendada sin emojis tampoco se guarda como propia.
    expect(isDefaultPaymentDetails(recommendedPaymentDetails({ emojis: false }))).toBe(true);
  });

  it("el aviso de espera va con el trato", () => {
    expect(waitNotice(10, "formal")).toBe("Una persona de nuestro equipo le responderá en unos 10 minutos.");
    expect(waitNotice(10)).toBe("Una persona de nuestro equipo te responderá en unos 10 minutos.");
    expect(waitNotice(0, "formal")).toBeNull();
  });
});
