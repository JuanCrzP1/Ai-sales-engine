import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Badge } from "../../components/ui/Feedback";
import type { Offering, SalesMode } from "../../domain/config/types";
import { formatPrice } from "../../lib/format";

interface OfferingListProps {
  offerings: Offering[];
  salesMode: SalesMode;
  onEdit: (offering: Offering) => void;
  onToggleAvailable: (offering: Offering) => void;
  onRemove: (offering: Offering) => void;
}

export function OfferingList({ offerings, salesMode, onEdit, onToggleAvailable, onRemove }: OfferingListProps) {
  return (
    <ul className="item-list" aria-label="Productos y servicios">
      {offerings.map((offering) => (
        <li key={offering.id} className="item-row">
          <div className="item-row__main">
            <span className="item-row__title">
              {offering.name.trim() || "Sin nombre"}
              {!offering.available && <Badge tone="neutral">No disponible</Badge>}
            </span>
            <span className="item-row__meta">{metaText(offering, salesMode)}</span>
          </div>
          <span className="item-row__price">{priceText(offering, salesMode)}</span>
          <span className="button-row">
            <Button variant="secondary" size="small" onClick={() => onEdit(offering)} aria-label={`Editar ${offering.name}`}>
              Editar
            </Button>
            <Button variant="ghost" size="small" onClick={() => onToggleAvailable(offering)}>
              {offering.available ? "Pausar" : "Activar"}
            </Button>
            <ConfirmButton confirmLabel="Sí, eliminar" onConfirm={() => onRemove(offering)}>
              Eliminar
            </ConfirmButton>
          </span>
        </li>
      ))}
    </ul>
  );
}

function metaText(offering: Offering, salesMode: SalesMode): string {
  const parts = [salesMode === "catalog" ? offering.category : "", offering.description].map((part) => part.trim()).filter(Boolean);
  return parts.join(" · ") || "Sin descripción";
}

function priceText(offering: Offering, salesMode: SalesMode): string {
  const price = formatPrice(offering.price, offering.currency);
  if (salesMode === "catalog" || offering.billing === "one_time") return price;
  return `${price} / mes`;
}
