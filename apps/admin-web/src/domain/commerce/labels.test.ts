import { describe, expect, it } from "vitest";
import { labelKey, nameProblem, shownLabels, toLabelColor, toggled, type LabelRef } from "./labels";

const VIP: LabelRef = { id: "l1", name: "VIP", color: "violet" };

describe("Las etiquetas de los clientes", () => {
  it("dos nombres que se leen igual son la misma etiqueta", () => {
    expect(labelKey("VIP")).toBe("vip");
    expect(labelKey("  Ví​p ")).toBe("vip");
    expect(labelKey("Niño   mayorista")).toBe("nino mayorista");
    expect(labelKey("Niña mayorista")).not.toBe(labelKey("Niño mayorista"));
  });

  it("dice por qué un nombre no sirve", () => {
    expect(nameProblem("   ", [])).toBe("Escribe el nombre de la etiqueta.");
    expect(nameProblem("x".repeat(31), [])).toMatch(/muy largo/);
    expect(nameProblem(" vip ", [VIP])).toBe("Ya tienes una etiqueta con ese nombre.");
    expect(nameProblem("Vip", [VIP], "l1")).toBeNull(); // es ella misma, al renombrarla
    expect(nameProblem("Mayorista", [VIP])).toBeNull();
  });

  it("pone y quita una etiqueta de la selección, y resume las que no caben", () => {
    expect(toggled(["a"], "b")).toEqual(["a", "b"]);
    expect(toggled(["a", "b"], "a")).toEqual(["b"]);
    expect(shownLabels(["a", "b", "c", "d", "e"])).toEqual({ shown: ["a", "b", "c"], more: 2 });
    expect(shownLabels(["a"])).toEqual({ shown: ["a"], more: 0 });
    expect(toLabelColor("green")).toBe("green");
    expect(toLabelColor("#ff0000")).toBe("slate");
  });
});
