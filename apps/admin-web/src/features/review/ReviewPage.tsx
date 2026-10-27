import { IssueList } from "../../components/config/IssueList";
import { SectionStatusBadge } from "../../components/config/SectionStatusBadge";
import { LinkButton } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { Card, PageHeader } from "../../components/ui/Layout";
import { sectionTitle } from "../../domain/sections";
import { splitBySeverity } from "../../domain/validation/issues";
import { sectionPath, stepLabel } from "../../navigation/navItems";
import { SectionPager } from "../../layout/SectionPager";
import { useConfig } from "../../state/useConfig";
import { buildSummary } from "./buildSummary";

export function ReviewPage() {
  const { config, issues, progress } = useConfig();
  const { errors, warnings } = splitBySeverity(issues);
  const summary = buildSummary(config);

  return (
    <>
      <PageHeader
        eyebrow={stepLabel("review")}
        title="Revisión de la configuración"
        description="Comprueba lo que has configurado antes de terminar."
      />

      <Alert tone="info" title="Configuración sin publicar">
        <p>
          Todavía no está conectada al asistente ni a ningún canal: revisarla aquí no la publica ni la pone en
          funcionamiento.
        </p>
      </Alert>

      {errors.length > 0 ? (
        <Alert tone="danger" title={`Faltan ${errors.length} ${errors.length === 1 ? "dato obligatorio" : "datos obligatorios"}`}>
          <IssueList issues={errors} />
        </Alert>
      ) : (
        <Alert tone="success" title="Todos los datos obligatorios están completos">
          <p>La configuración está lista para conectarse cuando la integración con el motor esté disponible.</p>
        </Alert>
      )}

      {warnings.length > 0 && (
        <Alert tone="warning" title={`${warnings.length} ${warnings.length === 1 ? "aviso" : "avisos"} para revisar`}>
          <IssueList issues={warnings} />
        </Alert>
      )}

      {summary.map((section) => {
        const sectionProgress = progress.sections.find((item) => item.id === section.id);
        return (
          <Card
            key={section.id}
            title={sectionTitle(section.id)}
            actions={
              <span className="button-row">
                {sectionProgress && <SectionStatusBadge progress={sectionProgress} />}
                <LinkButton to={sectionPath(section.id)} size="small">
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
