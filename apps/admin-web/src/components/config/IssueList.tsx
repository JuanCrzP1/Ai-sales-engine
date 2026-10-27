import { Link } from "react-router-dom";
import { sectionTitle } from "../../domain/sections";
import type { ValidationIssue } from "../../domain/validation/types";
import { sectionPath } from "../../navigation/navItems";

/** Lista de pendientes o avisos con acceso directo a la sección correspondiente. */
export function IssueList({ issues }: { issues: ValidationIssue[] }) {
  return (
    <ul>
      {issues.map((issue, index) => (
        <li key={`${issue.field}-${index}`}>
          <Link to={sectionPath(issue.section)}>{sectionTitle(issue.section)}</Link>: {issue.message}
        </li>
      ))}
    </ul>
  );
}
