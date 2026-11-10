import { LinkButton } from "../../components/ui/Button";
import { EmptyState } from "../../components/ui/Feedback";
import { SettingsCard } from "../../components/ui/SettingsCard";
import { isAvailable, offerEntries } from "../../domain/config/document";
import { sectionPath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useConfig } from "../../state/useConfig";

/** Productos o servicios que ofrece el negocio, tomados de la oferta (no se duplican aquí). */
export function OfferingsOverview() {
  const { document } = useConfig();
  const pathTo = useWorkspacePath();
  const available = offerEntries(document).filter(isAvailable);
  const manageLink = (
    <LinkButton to={pathTo(sectionPath("catalog"))} size="small">
      Administrar productos y servicios
    </LinkButton>
  );

  return (
    <SettingsCard icon="box" tone="sky" title="Productos o servicios que ofreces" description="Se administran en la pestaña de productos y servicios." actions={available.length > 0 ? manageLink : undefined} wide>
      {available.length === 0 ? (
        <EmptyState title="Todavía no hay productos ni servicios disponibles" description="Agrégalos en la sección de productos y servicios." action={manageLink} />
      ) : (
        <div className="overview-card__facts">
          {available.map((entry, index) => (
            <span key={`${entry.id}-${index}`} className="overview-card__fact">
              {entry.name.trim() || "Sin nombre"}
            </span>
          ))}
        </div>
      )}
    </SettingsCard>
  );
}
