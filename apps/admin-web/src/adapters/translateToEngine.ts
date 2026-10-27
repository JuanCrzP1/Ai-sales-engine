import type { AssistantConfig } from "../domain/config/types";
import { splitBySeverity } from "../domain/validation/issues";
import { validateConfig } from "../domain/validation/rules";
import type { ValidationIssue } from "../domain/validation/types";
import { checkEngineContract } from "./engineContract";
import { collectEngineNotices, type EngineNotice } from "./engineNotices";
import { toEngineSections } from "./engineRuntimeAdapter";
import type { EngineTenantSections } from "./engineTypes";

/**
 * Punto de entrada de la traducción al motor. CONTRATO PROVISIONAL: no se usa desde
 * la interfaz ni se conecta al motor; se revisará tras corregir los YAML.
 *
 * - Una configuración con errores de validación no se traduce (salvo `allowInvalid`).
 * - El resultado se comprueba contra el contrato mínimo conocido del motor.
 * - Siempre incluye los avisos de lo que se descarta, se fusiona o el motor no usa.
 */
export type EngineTranslation =
  | { status: "ok"; sections: EngineTenantSections; notices: EngineNotice[] }
  | { status: "invalid_config"; errors: ValidationIssue[] }
  | { status: "contract_violation"; violations: string[]; sections: EngineTenantSections; notices: EngineNotice[] };

export function translateToEngine(config: AssistantConfig, options: { allowInvalid?: boolean } = {}): EngineTranslation {
  const { errors } = splitBySeverity(validateConfig(config));
  if (errors.length > 0 && !options.allowInvalid) return { status: "invalid_config", errors };

  const sections = toEngineSections(config);
  const notices = collectEngineNotices(config);
  const violations = checkEngineContract(sections);
  return violations.length > 0 ? { status: "contract_violation", violations, sections, notices } : { status: "ok", sections, notices };
}
