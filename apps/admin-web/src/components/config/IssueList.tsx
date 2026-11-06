import { Link } from "react-router-dom";
import { sectionTitle } from "../../domain/sections";
import type { ValidationIssue } from "../../domain/validation/types";
import { sectionPath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";

/** Lista de pendientes o avisos con acceso directo a la sección correspondiente. */
export function IssueList({ issues }: { issues: ValidationIssue[] }) {
  const pathTo = useWorkspacePath();
  return (
    <ul>
      {issues.map((issue, index) => (
        <li key={`${issue.field}-${index}`}>
          <Link to={pathTo(sectionPath(issue.section))}>{sectionTitle(issue.section)}</Link>: {issue.label && `${issue.label}: `}
          {issue.message}
        </li>
      ))}
    </ul>
  );
}
