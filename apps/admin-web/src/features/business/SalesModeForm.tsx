import { useState } from "react";
import { Button } from "../../components/ui/Button";
import { RadioGroup } from "../../components/ui/ChoiceGroup";
import { Alert } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Layout";
import { offerEntries } from "../../domain/config/document";
import { OFFER_MODELS } from "../../domain/config/options";
import type { OfferModel } from "../../domain/config/types";
import { useConfig } from "../../state/useConfig";

/** Planes o catálogo: el contrato no admite ambos, así que cambiar convierte lo que hay y pide confirmación si hay datos. */
export function SalesModeForm() {
  const { document, actions } = useConfig();
  const [pending, setPending] = useState<OfferModel | null>(null);
  const hasEntries = offerEntries(document).length > 0;

  const choose = (model: OfferModel) => {
    if (model === document.offer.model) return;
    if (hasEntries) setPending(model);
    else actions.switchOfferModel(model);
  };

  return (
    <Card title="¿Cómo vendes?" description="Define cómo se presentan tus productos o servicios al cliente.">
      <RadioGroup legend="Forma de venta" name="sales-mode" options={OFFER_MODELS} value={document.offer.model} onChange={choose} />
      {pending && (
        <Alert tone="warning" title="Se convertirá lo que ya tienes">
          <p>
            {pending === "catalog"
              ? "Tus planes pasarán a ser productos de un catálogo con un solo precio. Se perderá lo que no aplica a un catálogo, como lo que no incluyen y los costos iniciales."
              : "Tus productos pasarán a ser planes con precio de pago único. Se perderán sus categorías, variantes y existencias."}
          </p>
          <div className="button-row">
            <Button
              size="small"
              variant="danger"
              onClick={() => {
                actions.switchOfferModel(pending);
                setPending(null);
              }}
            >
              Sí, convertir
            </Button>
            <Button size="small" variant="ghost" onClick={() => setPending(null)}>
              Cancelar
            </Button>
          </div>
        </Alert>
      )}
    </Card>
  );
}
