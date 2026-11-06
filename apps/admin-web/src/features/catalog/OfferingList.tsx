import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Badge } from "../../components/ui/Feedback";
import { categoryName, isAvailable, isCatalog, offerEntries, type OfferEntry } from "../../domain/config/document";
import { mainPlanAmount } from "../../domain/config/factories";
import type { BusinessDocument, CatalogItem, Plan } from "../../domain/config/types";
import { formatPrice } from "../../lib/format";

interface OfferingListProps {
  document: BusinessDocument;
  onEdit: (entry: OfferEntry) => void;
  onToggleAvailable: (entry: OfferEntry) => void;
  onRemove: (entry: OfferEntry) => void;
}

export function OfferingList({ document, onEdit, onToggleAvailable, onRemove }: OfferingListProps) {
  return (
    <ul className="item-list" aria-label="Productos y servicios">
      {offerEntries(document).map((entry) => (
        <li key={entry.id} className="item-row">
          <div className="item-row__main">
            <span className="item-row__title">
              {entry.name.trim() || "Sin nombre"}
              {!isAvailable(entry) && <Badge tone="neutral">No disponible</Badge>}
            </span>
            <span className="item-row__meta">{metaText(entry, document)}</span>
          </div>
          <span className="item-row__price">{priceText(entry, document)}</span>
          <span className="button-row">
            <Button variant="secondary" size="small" onClick={() => onEdit(entry)} aria-label={`Editar ${entry.name}`}>
              Editar
            </Button>
            <Button variant="ghost" size="small" onClick={() => onToggleAvailable(entry)}>
              {isAvailable(entry) ? "Pausar" : "Activar"}
            </Button>
            <ConfirmButton confirmLabel="Sí, eliminar" onConfirm={() => onRemove(entry)}>
              Eliminar
            </ConfirmButton>
          </span>
        </li>
      ))}
    </ul>
  );
}

function metaText(entry: OfferEntry, document: BusinessDocument): string {
  const category = isCatalog(document) ? categoryName(document, (entry as CatalogItem).category) : "";
  const parts = [category, entry.description ?? ""].map((part) => part.trim()).filter(Boolean);
  return parts.join(" · ") || "Sin descripción";
}

function priceText(entry: OfferEntry, document: BusinessDocument): string {
  if (isCatalog(document)) {
    const price = (entry as CatalogItem).prices[0];
    return price ? formatPrice(price.amount, price.currency) : "Sin precio";
  }
  const price = (entry as Plan).prices[0];
  if (!price) return "Sin precio";
  const { amount, period } = mainPlanAmount(price);
  return `${formatPrice(amount, price.currency)}${period ? ` / ${period}` : ""}`;
}
