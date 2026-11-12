import { LinkButton } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { ProgressRing } from "../../components/ui/ProgressRing";
import { sectionTitle } from "../../domain/sections";
import { OVERVIEW_ITEM, REVIEW_ITEM, sectionPath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useConfig } from "../../state/useConfig";

/** Cabecera destacada del inicio mientras falta configurar: título, progreso general y acceso a lo siguiente por completar. */
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

/** El inicio de un negocio ya configurado: su nombre arriba y, a continuación, lo del día (lo que se mira a diario). */
export function HomeHeader() {
  const { document } = useConfig();
  return (
    <header className="home-header">
      <p className="home-header__eyebrow">Inicio</p>
      <h1 className="home-header__title">{document.identity.name.trim() || "Tu negocio"}</h1>
    </header>
  );
}

/** Con todo configurado, el progreso ya no necesita una tarjeta grande: queda una franja con el estado y el siguiente paso. */
export function AssistantReady() {
  const { progress, publication } = useConfig();
  const pathTo = useWorkspacePath();
  // Por contenido, no por número de versión: guardar sin cambiar nada no deja cambios pendientes.
  const unpublished = publication === "pending" || publication === "never";

  return (
    <section className="ready-strip" aria-label="Estado del asistente">
      <span className="ready-strip__icon" aria-hidden="true">
        <Icon name="check" size={18} />
      </span>
      <div className="ready-strip__text">
        <strong>Tu asistente está configurado</strong>
        <span>
          {progress.completed} de {progress.total} secciones listas
          {publication === "never" ? " · todavía no lo has publicado" : unpublished ? " · tienes cambios sin publicar" : " · lo publicado es lo que responde"}
        </span>
      </div>
      {unpublished ? (
        <LinkButton to={pathTo(REVIEW_ITEM.path)} size="small">
          Revisar y publicar
        </LinkButton>
      ) : (
        <LinkButton to={pathTo(OVERVIEW_ITEM.path)} size="small" variant="ghost">
          Ver asistente
        </LinkButton>
      )}
    </section>
  );
}
