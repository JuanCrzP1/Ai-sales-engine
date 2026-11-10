import { useState } from "react";
import { Button, LinkButton } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import type { BusinessSummary } from "../../domain/config/types";
import { workspacePath } from "../../navigation/navItems";

interface BusinessListProps {
  businesses: BusinessSummary[];
  /** Sin esto no se ofrece eliminar (en la nube no se eliminan negocios). */
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
  const [deleting, setDeleting] = useState(false);
  const [typed, setTyped] = useState("");

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
          <Button variant="ghost" size="small" onClick={() => setDeleting(true)} aria-label={`Eliminar ${business.name}`}>
            Eliminar
          </Button>
        )}
      </span>
      {deleting && onRemove && (
        // Borra versiones y datos de pago sin posibilidad de recuperarlos: pide escribir el identificador.
        <form
          className="business-row__delete"
          onSubmit={(event) => {
            event.preventDefault();
            if (typed === business.slug) onRemove();
          }}
        >
          <TextField label={`Para confirmar, escribe ${business.slug}`} value={typed} onChange={setTyped} hint="Se borran todas sus versiones y sus datos de pago. No se puede deshacer." />
          <span className="button-row">
            <Button type="submit" variant="danger" size="small" disabled={typed !== business.slug}>
              Eliminar definitivamente
            </Button>
            <Button
              variant="ghost"
              size="small"
              onClick={() => {
                setDeleting(false);
                setTyped("");
              }}
            >
              Cancelar
            </Button>
          </span>
        </form>
      )}
    </li>
  );
}
