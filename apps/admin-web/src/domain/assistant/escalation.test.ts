import { SAMPLE_DOCUMENT } from "../../test/fixtures/sampleDocument";
import { MAX_ESCALATION_TOPIC_CHARS, MAX_ESCALATION_TOPICS } from "../../contracts/businessConfig.v1";
import type { BusinessDocument } from "../config/types";
import { validateDocument } from "../validation/rules";
import { escalationOf, escalationSummary, updatedEscalation, validateEscalation } from "./escalation";

const withRules = (escalation: BusinessDocument["escalation"]): BusinessDocument => ({ ...structuredClone(SAMPLE_DOCUMENT), escalation });
const fields = (document: BusinessDocument) => validateEscalation(document).map((issue) => issue.field);

describe("Cuándo pasar a una persona", () => {
  it("un documento sin la sección usa las reglas de siempre", () => {
    const document = withRules(undefined);
    expect(escalationOf(document)).toEqual({ on_request: "always", always_topics: [], never_topics: [], when_stuck: false, instructions: null });
    expect(fields(document)).toEqual([]);
    expect(escalationSummary(document)).toBe("Si piden una persona, la pasa de inmediato.");
  });

  it("si las reglas vuelven a ser las de siempre, la sección se quita (no aparece como cambio al publicar)", () => {
    const configured = withRules({ on_request: "offer_help_first" });
    expect(updatedEscalation(configured, { on_request: "always" })).toBeUndefined();
    expect(updatedEscalation(withRules(undefined), { when_stuck: true })).toEqual(expect.objectContaining({ when_stuck: true, on_request: "always" }));
    expect(updatedEscalation(withRules(undefined), { instructions: "   " })).toBeUndefined();
  });

  it("resume las reglas del negocio", () => {
    const document = withRules({ on_request: "offer_help_first", always_topics: ["reembolsos", "garantías"], when_stuck: true });
    expect(escalationSummary(document)).toBe("Si piden una persona, primero ofrece ayuda · 2 temas para tu equipo · también si la conversación se estanca.");
  });

  it("avisa como el contrato: temas repetidos, en las dos listas o demasiado largos", () => {
    expect(fields(withRules({ always_topics: ["Reembolsos", " reembolsos"] }))).toEqual(["escalation.always_topics"]);
    expect(fields(withRules({ always_topics: ["reembolsos"], never_topics: ["Reembolsos"] }))).toEqual(["escalation.never_topics"]);
    expect(fields(withRules({ never_topics: ["x".repeat(MAX_ESCALATION_TOPIC_CHARS + 1)] }))).toEqual(["escalation.never_topics"]);
    expect(fields(withRules({ always_topics: Array.from({ length: MAX_ESCALATION_TOPICS + 1 }, (_, n) => `tema ${n}`) }))).toEqual(["escalation.always_topics"]);
  });

  it("los errores llegan a la sección del asistente", () => {
    const issues = validateDocument({ document: withRules({ always_topics: ["a", "A"] }), paymentValues: {} });
    expect(issues.filter((issue) => issue.field.startsWith("escalation."))).toEqual([expect.objectContaining({ section: "assistant", severity: "error" })]);
  });
});
