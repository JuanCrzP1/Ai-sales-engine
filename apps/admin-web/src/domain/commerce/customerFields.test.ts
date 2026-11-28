import { describe, expect, it } from "vitest";
import { calendarDate, fieldNameProblem, inputValue, optionsFromText, optionsProblem, removedOptions, valueText } from "./customerFields";

describe("Los campos del cliente", () => {
  it("cada valor se lee como en Colombia", () => {
    expect(valueText("number", "1500000")).toBe("1.500.000");
    expect(valueText("number", "1200.5")).toBe("1.200,5");
    expect(valueText("date", "2026-11-29")).toBe("29 nov 2026");
    expect([valueText("yes_no", true), valueText("yes_no", false)]).toEqual(["Sí", "No"]);
    expect([valueText("text", null), valueText("choice", "Mayorista")]).toEqual([null, "Mayorista"]);
    // La fecha es un día del calendario: no se corre por la zona horaria.
    expect(calendarDate("2026-01-01")?.getDate()).toBe(1);
  });

  it("para editar, el número va con coma decimal y el sí o no como opción", () => {
    expect([inputValue("number", "1200.5"), inputValue("yes_no", true), inputValue("text", null)]).toEqual(["1200,5", "true", ""]);
  });

  it("las opciones van una por línea, sin repetir y al menos dos", () => {
    expect(optionsFromText(" Mayorista \n\n Al   detal ")).toEqual(["Mayorista", "Al detal"]);
    expect(optionsProblem(["Mayorista"])).toBe("Una lista necesita al menos 2 opciones, una por línea.");
    expect(optionsProblem(["VIP", "vip"])).toBe("«vip» está repetida.");
    expect(optionsProblem(["Mayorista", "Al detal"])).toBeNull();
    // «vip» escrita como «VIP» no se quita: es la misma.
    expect(removedOptions(["Mayorista", "vip"], ["VIP", "Al detal"])).toEqual(["Mayorista"]);
  });

  it("no hay dos campos que se lean igual", () => {
    const existing = [{ id: "f1", name: "Ciudad" }];
    expect(fieldNameProblem("  ciúdad ", existing)).toBe("Ya tienes un campo con ese nombre.");
    expect(fieldNameProblem("Ciudad", existing, "f1")).toBeNull();
    expect(fieldNameProblem(" ", existing)).toBe("Escribe el nombre del campo.");
  });
});
