import { Button, LinkButton } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Feedback";
import type { BusinessSummary } from "../../domain/config/types";
import { workspacePath } from "../../navigation/navItems";

interface BusinessListProps {
  businesses: BusinessSummary[];
  /** Pide eliminar un negocio (la confirmación es de quien lo llama). */
  onRemove?: (business: BusinessSummary) => void;
}

export function BusinessList({ businesses, onRemove }: BusinessListProps) {
  return (
    <ul className="item-list" aria-label="Negocios">
      {businesses.map((business) => (
        <BusinessRow key={business.slug} business={business} onRemove={onRemove ? () => onRemove(business) : undefined} />
      ))}
    </ul>
  );
}

function statusOf(business: BusinessSummary) {
  if (business.latestVersion === null) return <Badge tone="warning">Sin configurar</Badge>;
  if (business.publishedVersion === null) return <Badge tone="neutral">Sin publicar</Badge>;
  if (business.draftVersion !== null) return <Badge tone="accent">Cambios sin publicar</Badge>;
  return <Badge tone="success">Publicado</Badge>;
}

function BusinessRow({ business, onRemove }: { business: BusinessSummary; onRemove?: () => void }) {
  return (
    <li className="item-row business-row">
      <div className="item-row__main">
        <span className="item-row__title">
          {business.name}
          {statusOf(business)}
        </span>
        <span className="item-row__meta">
          Identificador: {business.slug}
          {business.latestVersion !== null && ` · Versión ${business.latestVersion}`}
        </span>
      </div>
      <span className="button-row">
        <LinkButton to={workspacePath(business.slug)} variant="primary" size="small" aria-label={`Abrir ${business.name}`}>
          Abrir
        </LinkButton>
        {onRemove && (
          <Button variant="ghost" size="small" onClick={onRemove} aria-label={`Eliminar ${business.name}`}>
            Eliminar
          </Button>
        )}
      </span>
    </li>
  );
}
