import { describe, expect, it } from "vitest";
import { assigneeLabel, describeEvent, initialsOf, nextStage, sinceText, type CustomerEvent } from "./customerCard";

const event = (overrides: Partial<CustomerEvent>): CustomerEvent => ({
  id: "e1", kind: "stage", source: "team", fromStage: "new", toStage: "ready", detail: null, actor: null, createdAt: "2026-11-28T10:00:00Z", ...overrides,
});

describe("La ficha del cliente", () => {
  it("cuenta cada cambio en una frase, con quién lo hizo", () => {
    expect(describeEvent(event({ source: "assistant", toStage: "interested" }))).toEqual({ title: "Pasó a «Interesado»", by: "lo movió el asistente", tone: "interested" });
    expect(describeEvent(event({ toStage: "lost", detail: "Le pareció caro", actor: "caro@negocio.com" }))).toEqual({
      title: "Pasó a «No compró» · Le pareció caro", by: "lo hizo caro@negocio.com", tone: "lost",
    });
    expect(describeEvent(event({ source: "sale", toStage: "customer", detail: "Plan Básico · COP 210.000", actor: "ana@negocio.com" })).by).toBe("por una venta que registró ana@negocio.com");
    expect(describeEvent(event({ source: "sale", toStage: "customer" })).by).toBe("por una venta registrada");
    expect(describeEvent(event({ kind: "value", detail: "COP 210.000" }))).toEqual({ title: "Valor: COP 210.000", by: "lo hizo tu equipo", tone: "value" });
    expect(describeEvent(event({ kind: "value" })).title).toBe("Se quitó el valor");
    expect(describeEvent(event({ kind: "owner", detail: "caro@negocio.com" })).title).toBe("caro@negocio.com quedó como responsable");
    expect(describeEvent(event({ kind: "owner" })).title).toBe("Quedó sin responsable");
  });

  it("sabe cuál es el paso siguiente de cada etapa", () => {
    expect(nextStage("new")).toBe("interested");
    expect(nextStage("payment")).toBe("customer");
    expect(nextStage("customer")).toBeNull();
    expect(nextStage("lost")).toBe("new");
  });

  it("dice hace cuánto está en su etapa", () => {
    expect(sinceText("ahora")).toBe("acaba de llegar aquí");
    expect(sinceText("hace 5 min")).toBe("aquí desde hace 5 min");
    expect(sinceText("ayer")).toBe("aquí desde ayer");
    expect(sinceText("12 nov")).toBe("aquí desde el 12 nov");
  });

  it("nombra a cada persona del equipo con su correo, su rol y sus iniciales", () => {
    expect(assigneeLabel({ email: "caro@negocio.com", role: "agent" })).toBe("caro@negocio.com · Asesor");
    expect(assigneeLabel({ email: null, role: "owner" })).toBe("Alguien del equipo · Dueño");
    expect(initialsOf("caro@negocio.com")).toBe("CA");
    expect(initialsOf("juan.perez@negocio.com")).toBe("JP");
    expect(initialsOf("")).toBe("?");
  });
});
