import { LinkButton } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { ProgressRing } from "../../components/ui/ProgressRing";
import { sectionTitle } from "../../domain/sections";
import { REVIEW_ITEM, sectionPath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useConfig } from "../../state/useConfig";

/** Cabecera destacada del inicio: título, progreso general y acceso a lo siguiente por completar. */
export function HomeHero() {
  const { progress, document } = useConfig();
  const pathTo = useWorkspacePath();
  const nextPending = progress.sections.find((section) => section.status === "pending");

  return (
    <header className="hero">
      <div className="hero__glow" aria-hidden="true" />
      <div className="hero__content">
        <p className="hero__eyebrow">
          <Icon name="sparkles" size={14} />
          {document.identity.name.trim() || "Negocio nuevo"}
        </p>
        <h1 className="hero__title">Configura tu asistente de ventas</h1>
        <p className="hero__description">Completa cada sección con la información de tu negocio y guarda los cambios. El asistente la usará para responder y vender por chat.</p>
        <div className="button-row">
          {nextPending ? (
            <LinkButton to={pathTo(sectionPath(nextPending.id))} variant="primary" className="button--on-dark">
              Continuar con {sectionTitle(nextPending.id)}
              <Icon name="arrowRight" size={16} />
            </LinkButton>
          ) : (
            <LinkButton to={pathTo(REVIEW_ITEM.path)} variant="primary" className="button--on-dark">
              Revisar y publicar
              <Icon name="arrowRight" size={16} />
            </LinkButton>
          )}
        </div>
      </div>
      <div className="hero__ring">
        <ProgressRing value={progress.completed} total={progress.total} />
        <span className="hero__ring-caption">secciones listas</span>
      </div>
    </header>
  );
}
