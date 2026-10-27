import { CONFIG_SECTIONS, type ConfigSectionId } from "../sections";
import type { ValidationIssue } from "./types";

export type SectionStatus = "complete" | "warnings" | "pending";

export interface SectionProgress {
  id: ConfigSectionId;
  status: SectionStatus;
  errors: number;
  warnings: number;
}

export interface ConfigProgress {
  sections: SectionProgress[];
  completed: number;
  total: number;
  /** Lista para revisión: sin errores en ninguna sección. */
  ready: boolean;
}

export function computeProgress(issues: ValidationIssue[]): ConfigProgress {
  const sections = CONFIG_SECTIONS.map(({ id }): SectionProgress => {
    const own = issues.filter((issue) => issue.section === id);
    const errors = own.filter((issue) => issue.severity === "error").length;
    const warnings = own.length - errors;
    const status: SectionStatus = errors > 0 ? "pending" : warnings > 0 ? "warnings" : "complete";
    return { id, status, errors, warnings };
  });
  const completed = sections.filter((section) => section.status !== "pending").length;
  return { sections, completed, total: sections.length, ready: completed === sections.length };
}
