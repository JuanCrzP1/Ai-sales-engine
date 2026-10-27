import { LinkButton } from "../../components/ui/Button";
import { EmptyState } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Layout";
import { sectionPath } from "../../navigation/navItems";
import { useConfig } from "../../state/useConfig";

/** Productos o servicios que ofrece el negocio, tomados del catálogo (no se duplican aquí). */
export function OfferingsOverview() {
  const { config } = useConfig();
  const available = config.offerings.filter((offering) => offering.available);
  const manageLink = (
    <LinkButton to={sectionPath("catalog")} size="small">
      Administrar productos y servicios
    </LinkButton>
  );

  return (
    <Card title="Productos o servicios que ofreces" actions={available.length > 0 ? manageLink : undefined}>
      {available.length === 0 ? (
        <EmptyState
          title="Todavía no hay productos ni servicios disponibles"
          description="Agrégalos en la sección de productos y servicios."
          action={manageLink}
        />
      ) : (
        <p>{available.map((offering) => offering.name.trim() || "Sin nombre").join(" · ")}</p>
      )}
    </Card>
  );
}
