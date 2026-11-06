import { IssueList } from "../../components/config/IssueList";
import { SectionStatusBadge } from "../../components/config/SectionStatusBadge";
import { LinkButton } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { Card, PageHeader } from "../../components/ui/Layout";
import { sectionTitle } from "../../domain/sections";
import { splitBySeverity } from "../../domain/validation/issues";
import { SectionPager } from "../../layout/SectionPager";
import { sectionPath, stepLabel } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useConfig } from "../../state/useConfig";
import { buildSummary } from "./buildSummary";
import { PublishCard } from "./PublishCard";

export function ReviewPage() {
  const { document, issues, progress } = useConfig();
  const pathTo = useWorkspacePath();
  const { errors, warnings } = splitBySeverity(issues);
  const summary = buildSummary(document);

  return (
    <>
      <PageHeader eyebrow={stepLabel("review")} title="Revisión y publicación" description="Comprueba lo que has configurado, guárdalo y publícalo." />

      {errors.length > 0 ? (
        <Alert tone="danger" title={errors.length === 1 ? "Falta 1 dato obligatorio" : `Faltan ${errors.length} datos obligatorios`}>
          <IssueList issues={errors} />
        </Alert>
      ) : (
        <Alert tone="success" title="Todos los datos obligatorios están completos" />
      )}

      {warnings.length > 0 && (
        <Alert tone="warning" title={`${warnings.length} ${warnings.length === 1 ? "aviso" : "avisos"} para revisar`}>
          <IssueList issues={warnings} />
        </Alert>
      )}

      <PublishCard />

      {summary.map((section) => {
        const sectionProgress = progress.sections.find((item) => item.id === section.id);
        return (
          <Card
            key={section.id}
            title={sectionTitle(section.id)}
            actions={
              <span className="button-row">
                {sectionProgress && <SectionStatusBadge progress={sectionProgress} />}
                <LinkButton to={pathTo(sectionPath(section.id))} size="small">
                  Editar
                </LinkButton>
              </span>
            }
          >
            <dl className="summary-list">
              {section.rows.map((row, index) => (
                <div key={`${row.label}-${index}`} className="summary-list__row">
                  <dt>{row.label}</dt>
                  <dd>{row.value}</dd>
                </div>
              ))}
            </dl>
          </Card>
        );
      })}

      <SectionPager current="review" />
    </>
  );
}
