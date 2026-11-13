import { Link } from "react-router-dom";
import { IssueList } from "../../components/config/IssueList";
import { SectionStatusBadge } from "../../components/config/SectionStatusBadge";
import { Alert } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { Card } from "../../components/ui/Layout";
import { CONFIG_SECTIONS } from "../../domain/sections";
import { splitBySeverity } from "../../domain/validation/issues";
import { NAV_ICONS } from "../../layout/navIcons";
import { SectionPager } from "../../layout/SectionPager";
import { REVIEW_ITEM, sectionPath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useConfig } from "../../state/useConfig";
import { useCan } from "../../state/roleContext";
import { ActivityOverview } from "./ActivityOverview";
import { AssistantSummary } from "./AssistantSummary";
import { AssistantReady, HomeHeader, HomeHero } from "./HomeHero";
import { AgentHome } from "./AgentHome";

export function HomePage() {
  // Un asesor atiende: su inicio es lo del día, sin el estado de la configuración (que no puede cambiar).
  if (!useCan("configure")) return <AgentHome />;
  return <OwnerHome />;
}

function OwnerHome() {
  const { progress, issues, meta } = useConfig();
  const pathTo = useWorkspacePath();
  const { errors, warnings } = splitBySeverity(issues);
  // Con todo configurado y guardado, lo de cada día va primero y el progreso queda en una franja pequeña.
  const ready = progress.total > 0 && progress.completed === progress.total && errors.length === 0 && meta.latestVersion !== null;

  return (
    <>
      {ready ? <HomeHeader /> : <HomeHero />}

      <ActivityOverview />

      {ready && <AssistantReady />}

      <AssistantSummary />

      {meta.latestVersion === null && (
        <Alert tone="info" title="Este negocio aún no se ha guardado">
          <p>El servidor acepta la configuración cuando tiene lo indispensable: los datos del negocio y al menos un producto o servicio. Hasta entonces, lo que escribas está solo en esta pestaña.</p>
        </Alert>
      )}

      <Card title="Estado de la configuración">
        {errors.length > 0 ? (
          <Alert tone="warning" title={`Tienes ${errors.length} ${errors.length === 1 ? "dato pendiente" : "datos pendientes"}`}>
            <IssueList issues={errors.slice(0, 5)} />
            {errors.length > 5 && <p>Y {errors.length - 5} más en la revisión.</p>}
          </Alert>
        ) : (
          <Alert tone="success" title="No hay datos obligatorios pendientes">
            {warnings.length > 0 && <p>{warnings.length === 1 ? "Hay 1 aviso que conviene revisar" : `Hay ${warnings.length} avisos que conviene revisar`} antes de publicar.</p>}
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
              <Link key={section.id} to={pathTo(sectionPath(section.id))} className="section-card" style={{ animationDelay: `${index * 60}ms` }}>
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
          <Link to={pathTo(REVIEW_ITEM.path)} className="section-card section-card--highlight">
            <span className="section-card__top">
              <span className="section-card__icon section-card__icon--review">
                <Icon name="check" size={20} />
              </span>
            </span>
            <span className="section-card__title">{REVIEW_ITEM.title}</span>
            <span className="section-card__summary">Comprueba todo, guárdalo y publícalo.</span>
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
