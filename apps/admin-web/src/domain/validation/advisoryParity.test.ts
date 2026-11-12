import cases from "../../../../../project/config/contracts/v1/advisory-cases.json";
import { SAMPLE_DOCUMENT } from "../../test/fixtures/sampleDocument";
import type { BusinessDocument } from "../config/types";
import { LIVE_ADVISORY_CODES } from "./liveAdvisories";
import { validateDocument } from "./rules";

/**
 * Los avisos que el panel calcula en vivo son los mismos que el servidor da en su diagnóstico (lo que lee el agente por MCP):
 * mismo campo y mismo texto. Los casos son los de `project/config/contracts/v1/advisory-cases.json`, que el servidor prueba en
 * `tests/test_business_config_advisories.py`.
 */

/** Como update_business_config: los objetos se combinan, las listas se reemplazan y null quita el dato. */
function merged(base: unknown, changes: unknown): unknown {
  if (changes === null || typeof changes !== "object" || Array.isArray(changes) || base === null || typeof base !== "object" || Array.isArray(base)) {
    return structuredClone(changes);
  }
  const result: Record<string, unknown> = structuredClone(base as Record<string, unknown>);
  for (const [key, value] of Object.entries(changes as Record<string, unknown>)) {
    if (value === null) delete result[key];
    else result[key] = merged(result[key], value);
  }
  return result;
}

describe("avisos en vivo, iguales en el panel y en el servidor", () => {
  it("los casos cubren todos los avisos compartidos", () => {
    expect(cases.cases.map((item) => item.code).sort()).toEqual([...LIVE_ADVISORY_CODES].sort());
  });

  it("un documento completo no tiene ninguno", () => {
    const fields = new Set(cases.cases.map((item) => item.field));
    const warnings = validateDocument({ document: SAMPLE_DOCUMENT, paymentValues: {} }).filter((issue) => issue.severity === "warning");
    expect(warnings.filter((issue) => fields.has(issue.field))).toEqual([]);
  });

  it.each(cases.cases.map((item) => [item.code, item] as const))("%s: mismo campo y mismo texto", (_code, item) => {
    const document = merged(SAMPLE_DOCUMENT, item.changes) as BusinessDocument;
    const warnings = validateDocument({ document, paymentValues: {} }).filter((issue) => issue.severity === "warning" && issue.field === item.field);
    expect(warnings.map((issue) => issue.message)).toEqual([item.message]);
  });
});
