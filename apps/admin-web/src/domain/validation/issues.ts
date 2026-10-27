import type { ValidationIssue } from "./types";

/** Incidencias de un campo concreto (por ejemplo, "business.name"). */
export function issuesFor(issues: ValidationIssue[], field: string): ValidationIssue[] {
  return issues.filter((issue) => issue.field === field);
}

export function splitBySeverity(issues: ValidationIssue[]): { errors: ValidationIssue[]; warnings: ValidationIssue[] } {
  return {
    errors: issues.filter((issue) => issue.severity === "error"),
    warnings: issues.filter((issue) => issue.severity === "warning"),
  };
}
