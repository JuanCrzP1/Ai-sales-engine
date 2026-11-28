import { describe, expect, it } from "vitest";
import { durationText, nextStep, recommendedFollowUp, splitMinutes, stepProblem } from "./followUp";

describe("seguimiento", () => {
  it("los recomendados salen a la hora, al día siguiente y a los 3 días, con el trato y los emojis del negocio", () => {
    const tu = recommendedFollowUp();
    expect(tu.map((step) => step.after_minutes)).toEqual([60, 1440, 4320]);
    expect(tu[0]!.message).toBe("¿Pudiste ver la información? Si te quedó alguna duda, aquí estoy para ayudarte. 😊");
    const usted = recommendedFollowUp({ formality: "formal", emojis: false });
    expect(usted[0]!.message).toBe("¿Pudo ver la información? Si le quedó alguna duda, aquí estoy para ayudarle.");
    expect(usted[1]!.message).toBe("Hola de nuevo ¿Seguimos con lo que estaba viendo? Cuando quiera le ayudo a terminar.");
    expect(usted.some((step) => /[😊👋]/u.test(step.message))).toBe(false);
  });

  it("los tiempos se muestran en la unidad que los divide exacto", () => {
    expect(splitMinutes(1440)).toEqual({ amount: 1, unit: "days" });
    expect(splitMinutes(120)).toEqual({ amount: 2, unit: "hours" });
    expect(splitMinutes(90)).toEqual({ amount: 90, unit: "minutes" });
    expect([durationText(60), durationText(4320), durationText(45)]).toEqual(["1 hora", "3 días", "45 minutos"]);
  });

  it("cada mensaje sale después del anterior, entre media hora y 30 días", () => {
    const steps = [{ after_minutes: 60, message: "a" }, { after_minutes: 60, message: "b" }];
    expect(stepProblem(steps, 0)).toBeNull();
    expect(stepProblem(steps, 1)).toBe("Debe salir después del mensaje anterior.");
    expect(stepProblem([{ after_minutes: 10, message: "a" }], 0)).toBe("Como pronto, media hora después.");
    expect(stepProblem([{ after_minutes: 31 * 24 * 60, message: "a" }], 0)).toBe("Como tarde, 30 días después.");
    expect(nextStep(steps)).toEqual({ after_minutes: 60 + 1440, message: "" });
  });
});
