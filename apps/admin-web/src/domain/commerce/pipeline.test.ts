import { describe, expect, it } from "vitest";
import { boughtText, customerName, daysText, moneyTotals, moveKind, percent } from "./pipeline";

describe("El tablero de Clientes", () => {
  it("sabe cómo se hace cada cambio de etapa", () => {
    expect(moveKind("ready", "ready")).toBe("none");
    expect(moveKind("new", "ready")).toBe("direct");
    expect(moveKind("lost", "interested")).toBe("direct");
    expect(moveKind("ready", "lost")).toBe("reason");
    expect(moveKind("payment", "customer")).toBe("sale");
  });

  it("dice los números como los leería el dueño", () => {
    expect(percent(0.714)).toBe("71 %");
    expect(percent(1)).toBe("100 %");
    expect(percent(null)).toBeNull();
    expect(daysText(3)).toBe("3 días");
    expect(daysText(1)).toBe("1 día");
    expect(daysText(1.5)).toBe("1,5 días");
    expect(daysText(0.4)).toBe("menos de 1 día");
  });

  it("nunca mezcla monedas: los pesos primero y las demás aparte", () => {
    const totals = moneyTotals({ USD: "20.00", COP: "50000.00" });
    expect(totals.main).toMatch(/50\.000/);
    expect(totals.rest).toHaveLength(1);
    expect(totals.rest[0]).toMatch(/20,00/);
    expect(moneyTotals({})).toEqual({ main: null, rest: [] });
  });

  it("resume lo que lleva comprado y nombra a quien no tiene nombre por su número", () => {
    expect(boughtText({ purchases: 0, spent: {} })).toBeNull();
    expect(boughtText({ purchases: 2, spent: { COP: "210000.00" } })).toMatch(/^Lleva .*210\.000 · 2 compras$/);
    expect(boughtText({ purchases: 1, spent: { COP: "40000.00" } })).toMatch(/1 compra$/);
    expect(customerName({ name: null, contact: "573001112233" })).toBe("+573001112233");
    expect(customerName({ name: "Laura", contact: "573001112233" })).toBe("Laura");
  });
});
