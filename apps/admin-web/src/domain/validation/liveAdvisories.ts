import type { Diagnostic } from "../config/types";

/**
 * Los avisos que el panel calcula en vivo (`rules.ts`) y que el servidor también da, con el mismo campo y el mismo texto, para que
 * el agente que trabaja por MCP vea lo mismo que la persona. Los casos compartidos: `project/config/contracts/v1/advisory-cases.json`.
 */
export const LIVE_ADVISORY_CODES = ["sin_direccion", "cuentas_repetidas", "sin_medios_de_pago", "sin_problemas_del_cliente", "sin_mensaje_de_pago_reportado"] as const;

/** Diagnósticos del servidor que el panel ya muestra en vivo con sus propias palabras: no se repiten en «Publicar». */
const ALSO_SHOWN_LIVE = ["promocion_vencida", "recomienda_oferta_no_disponible", "sin_canales_de_atencion", "transferencias_sin_cuentas_activas", "cierre_por_link_sin_link"];

const SHOWN_LIVE = new Set<string>([...LIVE_ADVISORY_CODES, ...ALSO_SHOWN_LIVE]);

/** Lo que el servidor diagnostica y el panel no muestra ya en vivo. */
export function serverOnlyDiagnostics(diagnostics: Diagnostic[]): Diagnostic[] {
  return diagnostics.filter((item) => !SHOWN_LIVE.has(item.code));
}
