import { Link } from "react-router-dom";
import { SectionStatusBadge } from "../../components/config/SectionStatusBadge";
import { LinkButton } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { ProgressRing } from "../../components/ui/ProgressRing";
import type { CardTone } from "../../components/ui/SettingsCard";
import { isAvailable, isCatalog, offerEntries, paymentOptionsCount } from "../../domain/config/document";
import type { BusinessDocument } from "../../domain/config/types";
import { CONFIG_SECTIONS, sectionTitle, type ConfigSectionId } from "../../domain/sections";
import { PLAYGROUND_ITEM, REVIEW_ITEM, sectionPath, stepLabel } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { NAV_ICONS } from "../../layout/navIcons";
import { useConfig } from "../../state/useConfig";

const TONES: Record<ConfigSectionId, CardTone> = { business: "indigo", catalog: "sky", payments: "emerald", assistant: "violet", messages: "amber" };

const plural = (count: number, one: string, many: string) => `${count} ${count === 1 ? one : many}`;

/** Dos o tres datos de cada sección, para ver de un vistazo qué tiene configurado. */
function facts(id: ConfigSectionId, document: BusinessDocument): string[] {
  switch (id) {
    case "business": {
      const city = document.identity.location?.city?.trim();
      return [document.identity.industry.trim(), city ? `En ${city}` : "", document.identity.opening_hours?.length ? "Con horario" : ""].filter(Boolean);
    }
    case "catalog": {
      const entries = offerEntries(document);
      const catalog = isCatalog(document);
      return [
        plural(entries.filter(isAvailable).length, catalog ? "producto disponible" : "plan disponible", catalog ? "productos disponibles" : "planes disponibles"),
        document.fulfillment?.delivery?.available ? "Con domicilio" : "",
        document.fulfillment?.shipping?.available ? "Con envíos" : "",
      ].filter(Boolean);
    }
    case "payments":
      return [
        plural(paymentOptionsCount(document), "medio de pago", "medios de pago"),
        document.terms.promotions?.length ? plural(document.terms.promotions.length, "promoción", "promociones") : "",
        document.terms.financing?.available ? "Con financiación" : "",
      ].filter(Boolean);
    case "assistant":
      return [
        document.response_style.tone?.trim() ? `Tono ${document.response_style.tone.trim()}` : "",
        plural(document.knowledge.faqs?.length ?? 0, "pregunta frecuente", "preguntas frecuentes"),
      ].filter(Boolean);
    case "messages":
      return [
        document.messages.welcome.enabled ? "Bienvenida activa" : "Bienvenida de la IA",
        document.capabilities.service_channels?.length ? plural(document.capabilities.service_channels.length, "canal", "canales") : "",
      ].filter(Boolean);
  }
}

/** El Asistente IA de un vistazo: cada sección en una tarjeta con su estado, y los accesos a probarlo y publicarlo. */
export function AssistantOverviewPage() {
  const { document, progress } = useConfig();
  const pathTo = useWorkspacePath();
  const nextPending = progress.sections.find((section) => section.status === "pending");
  const name = document.identity.name.trim() || "Tu negocio";

  return (
    <>
      <header className="overview-hero">
        <div className="overview-hero__text">
          <p className="overview-hero__eyebrow">{name}</p>
          <h1 className="overview-hero__title">Tu asistente, sección por sección</h1>
          <p className="overview-hero__description">
            Completa cada tarjeta con la información de tu negocio. Lo esencial está primero; las opciones avanzadas son para afinar cuando quieras.
          </p>
          <div className="overview-hero__actions">
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
            <LinkButton to={pathTo(PLAYGROUND_ITEM.path)} variant="secondary" className="button--on-dark">
              Probar el asistente
            </LinkButton>
          </div>
        </div>
        <div className="overview-hero__progress">
          <ProgressRing value={progress.completed} total={progress.total} />
        </div>
      </header>

      <section className="overview-grid" aria-label="Secciones del asistente">
        {CONFIG_SECTIONS.map((section) => {
          const status = progress.sections.find((entry) => entry.id === section.id);
          const tone = TONES[section.id];
          return (
            <Link key={section.id} to={pathTo(sectionPath(section.id))} className="overview-card">
              <div className="overview-card__top">
                <span className={`settings-card__icon settings-card__icon--${tone}`}>
                  <Icon name={NAV_ICONS[section.id]} size={20} />
                </span>
                {status && <SectionStatusBadge progress={status} />}
              </div>
              <p className="overview-card__step">{stepLabel(section.id)}</p>
              <h2 className="overview-card__title">{section.title}</h2>
              <p className="overview-card__summary">{section.summary}</p>
              <div className="overview-card__facts">
                {facts(section.id, document).map((fact) => (
                  <span key={fact} className="overview-card__fact">
                    {fact}
                  </span>
                ))}
              </div>
              <span className="overview-card__cta">
                Configurar <Icon name="arrowRight" size={14} />
              </span>
            </Link>
          );
        })}
        <div className="overview-card overview-card--highlight">
          <div className="overview-card__top">
            <span className="settings-card__icon settings-card__icon--emerald">
              <Icon name="send" size={20} />
            </span>
          </div>
          <p className="overview-card__step">Antes de vender</p>
          <h2 className="overview-card__title">Probar y publicar</h2>
          <p className="overview-card__summary">
            Conversa con tu asistente como si fueras un cliente y, cuando te guste cómo responde, publica: desde ese momento atiende con
            la nueva versión.
          </p>
          <div className="overview-card__links">
            <Link to={pathTo(PLAYGROUND_ITEM.path)} className="overview-card__cta">
              <Icon name="flask" size={14} /> Probar el asistente
            </Link>
            <Link to={pathTo(REVIEW_ITEM.path)} className="overview-card__cta">
              <Icon name="check" size={14} /> Revisar y publicar
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
