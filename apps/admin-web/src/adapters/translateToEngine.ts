import type { AssistantConfig } from "../domain/config/types";
import { splitBySeverity } from "../domain/validation/issues";
import { validateConfig } from "../domain/validation/rules";
import type { ValidationIssue } from "../domain/validation/types";
import { toBusinessConfig, type ContractTranslation } from "./contractAdapter";
import { collectEngineNotices, type EngineNotice } from "./engineNotices";

/**
 * Punto de entrada de la traducción al motor: produce el documento del contrato global
 * (BusinessConfig v1) y, aparte, los datos de pago sensibles. Todavía no se envía a ningún
 * servidor; el motor valida de nuevo el documento al recibirlo.
 *
 * - Una configuración con errores de validación no se traduce (salvo `allowInvalid`).
 * - Siempre incluye los avisos de lo que se descarta, se fusiona o el motor no usa.
 */
export type EngineTranslation =
  | ({ status: "ok"; notices: EngineNotice[] } & ContractTranslation)
  | { status: "invalid_config"; errors: ValidationIssue[] };

export function translateToEngine(
  config: AssistantConfig,
  tenantSlug: string,
  options: { allowInvalid?: boolean } = {},
): EngineTranslation {
  const { errors } = splitBySeverity(validateConfig(config));
  if (errors.length > 0 && !options.allowInvalid) return { status: "invalid_config", errors };
  return { status: "ok", ...toBusinessConfig(config, tenantSlug), notices: collectEngineNotices(config) };
}
