import type { ConfigSectionId } from "../sections";

export type IssueSeverity = "error" | "warning";

export interface ValidationIssue {
  section: ConfigSectionId;
  /** Identificador estable del campo (por ejemplo, "business.name" o "offerings.<id>.price"). */
  field: string;
  severity: IssueSeverity;
  message: string;
}
