import type { ConfigSectionId } from "../sections";

export type IssueSeverity = "error" | "warning";

export interface ValidationIssue {
  section: ConfigSectionId;
  /** Identificador estable del campo (por ejemplo, "business.name" o "offerings.<id>.price"). */
  field: string;
  severity: IssueSeverity;
  message: string;
  /** Nombre del campo, para listar el error fuera de su formulario cuando el mensaje no lo dice (los del servidor). */
  label?: string;
}
