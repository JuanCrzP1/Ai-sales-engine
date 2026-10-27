import { Link } from "react-router-dom";
import { IssueList } from "../../components/config/IssueList";
import { SectionStatusBadge } from "../../components/config/SectionStatusBadge";
import { Alert } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { Card } from "../../components/ui/Layout";
import { CONFIG_SECTIONS } from "../../domain/sections";
import { splitBySeverity } from "../../domain/validation/issues";
import { NAV_ICONS } from "../../layout/navIcons";
import { REVIEW_ITEM, sectionPath } from "../../navigation/navItems";
import { SectionPager } from "../../layout/SectionPager";
import { useConfig } from "../../state/useConfig";
import { AssistantSummary } from "./AssistantSummary";
import { HomeHero } from "./HomeHero";

export function HomePage() {
  const { progress, issues } = useConfig();
  const { errors, warnings } = splitBySeverity(issues);

  return (
    <>
      <HomeHero />

      <AssistantSummary />

      <Card title="Estado de la configuración">
        {errors.length > 0 ? (
          <Alert tone="warning" title={`Tienes ${errors.length} ${errors.length === 1 ? "dato pendiente" : "datos pendientes"}`}>
            <IssueList issues={errors.slice(0, 5)} />
            {errors.length > 5 && <p>Y {errors.length - 5} más en la revisión.</p>}
          </Alert>
        ) : (
          <Alert tone="success" title="No hay datos obligatorios pendientes">
            {warnings.length > 0 && <p>Hay {warnings.length} avisos que conviene revisar antes de terminar.</p>}
          </Alert>
        )}
      </Card>

      <section aria-labelledby="secciones-titulo" className="home-sections">
        <h2 id="secciones-titulo" className="section-heading">
          Secciones
        </h2>
        <div className="grid-cards">
          {CONFIG_SECTIONS.map((section, index) => {
            const sectionProgress = progress.sections.find((item) => item.id === section.id);
            return (
              <Link
                key={section.id}
                to={sectionPath(section.id)}
                className="section-card"
                style={{ animationDelay: `${index * 60}ms` }}
              >
                <span className="section-card__top">
                  <span className={`section-card__icon section-card__icon--${section.id}`}>
                    <Icon name={NAV_ICONS[section.id]} size={20} />
                  </span>
                  {sectionProgress && <SectionStatusBadge progress={sectionProgress} />}
                </span>
                <span className="section-card__title">{section.title}</span>
                <span className="section-card__summary">{section.summary}</span>
                <span className="section-card__cta">
                  Abrir
                  <Icon name="arrowRight" size={14} />
                </span>
              </Link>
            );
          })}
          <Link to={REVIEW_ITEM.path} className="section-card section-card--highlight">
            <span className="section-card__top">
              <span className="section-card__icon section-card__icon--review">
                <Icon name="check" size={20} />
              </span>
            </span>
            <span className="section-card__title">{REVIEW_ITEM.title}</span>
            <span className="section-card__summary">Comprueba todo antes de terminar y revisa los datos pendientes.</span>
            <span className="section-card__cta">
              Revisar
              <Icon name="arrowRight" size={14} />
            </span>
          </Link>
        </div>
      </section>

      <SectionPager current="home" />
    </>
  );
}
