import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import type { Promotion } from "../../domain/config/types";
import { optionalList } from "../../domain/config/document";
import { MAX_PROMOTIONS } from "../../domain/config/engineLimits";
import { useFieldIssue, useSection } from "../../state/useConfig";

/** Únicas promociones o descuentos que el asistente puede ofrecer. */
export function PromotionsForm() {
  const [terms, update] = useSection("terms");
  const listIssue = useFieldIssue("terms.promotions");
  const promotions = terms.promotions ?? [];
  const set = (next: Promotion[]) => update({ promotions: optionalList(next) });

  return (
    <Card icon="tag" tone="rose" title="Promociones" description="El asistente solo ofrece las que estén aquí y sigan vigentes.">
      {listIssue && <p className={`field__message field__message--${listIssue.severity}`}>{listIssue.message}</p>}
      {promotions.length === 0 && <p className="field__hint">Aún no hay promociones.</p>}
      {promotions.map((promotion, index) => (
        <PromotionRow
          key={index}
          promotion={promotion}
          index={index}
          onChange={(patch) => set(promotions.map((item, position) => (position === index ? { ...item, ...patch } : item)))}
          onRemove={() => set(promotions.filter((_, position) => position !== index))}
        />
      ))}
      <div>
        <Button variant="secondary" disabled={promotions.length >= MAX_PROMOTIONS} onClick={() => set([...promotions, { name: "", details: "", valid_until: null }])}>
          Agregar promoción
        </Button>
      </div>
    </Card>
  );
}

function PromotionRow({ promotion, index, onChange, onRemove }: { promotion: Promotion; index: number; onChange: (patch: Partial<Promotion>) => void; onRemove: () => void }) {
  const field = (name: string) => `terms.promotions.${index}.${name}`;
  const nameIssue = useFieldIssue(field("name"));
  const detailsIssue = useFieldIssue(field("details"));
  const untilIssue = useFieldIssue(field("valid_until"));

  return (
    <fieldset className="subcard">
      <legend className="field__label">Promoción {index + 1}</legend>
      <div className="grid-2">
        <TextField label="Nombre" required value={promotion.name} onChange={(name) => onChange({ name })} placeholder="Ej.: Lanzamiento" issue={nameIssue} />
        <TextField label="Vigente hasta (opcional)" type="date" value={promotion.valid_until ?? ""} onChange={(until) => onChange({ valid_until: until || null })} issue={untilIssue} />
      </div>
      <TextField label="Qué incluye y a qué aplica" required value={promotion.details} onChange={(details) => onChange({ details })} placeholder="Ej.: 10 % en el primer mes" issue={detailsIssue} />
      <div>
        <ConfirmButton confirmLabel="Sí, quitar" onConfirm={onRemove}>
          Quitar promoción
        </ConfirmButton>
      </div>
    </fieldset>
  );
}
