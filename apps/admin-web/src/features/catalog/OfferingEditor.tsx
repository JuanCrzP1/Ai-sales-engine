import { useEffect, useId, useRef } from "react";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { NumberField, SelectField, TextAreaField, TextField } from "../../components/ui/FormFields";
import { ListEditor } from "../../components/ui/ListEditor";
import { Toggle } from "../../components/ui/Toggle";
import type { CatalogItem, ItemPrice, Plan, PlanPrice } from "../../domain/config/types";
import { optionalList, optionalText, type OfferEntry } from "../../domain/config/document";
import { TEXT_LIMITS } from "../../domain/config/engineLimits";
import { DEFAULT_CURRENCY } from "../../domain/config/factories";
import { currencyOptions } from "../../domain/config/options";
import { issuesFor } from "../../domain/validation/issues";
import type { ValidationIssue } from "../../domain/validation/types";

interface OfferingEditorProps {
  draft: OfferEntry;
  categoryName: string;
  isNew: boolean;
  issues: ValidationIssue[];
  catalog: boolean;
  categorySuggestions: string[];
  profiles: string[];
  onChange: (patch: Partial<Plan & CatalogItem>) => void;
  onChangeCategory: (name: string) => void;
  onSave: () => void;
  onCancel: () => void;
}

export function OfferingEditor({ draft, categoryName, isNew, issues, catalog, categorySuggestions, profiles, onChange, onChangeCategory, onSave, onCancel }: OfferingEditorProps) {
  const titleId = useId();
  const listId = useId();
  const containerRef = useRef<HTMLFormElement>(null);
  const issue = (field: string) => issuesFor(issues, field)[0];
  const pricesIssue = issue("prices");

  useEffect(() => {
    containerRef.current?.querySelector<HTMLInputElement>("input")?.focus();
  }, [draft.id]);

  return (
    <form
      ref={containerRef}
      className="card"
      aria-labelledby={titleId}
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        onSave();
      }}
    >
      <h2 className="card__title" id={titleId}>
        {isNew ? (catalog ? "Nuevo producto" : "Nuevo plan o servicio") : `Editar: ${draft.name || "sin nombre"}`}
      </h2>

      <div className="grid-2">
        <TextField label="Nombre" required value={draft.name} onChange={(name) => onChange({ name })} issue={issue("name")} />
        {catalog ? (
          <>
            <TextField
              label="Categoría"
              required
              value={categoryName}
              onChange={onChangeCategory}
              placeholder="Ej.: Bebidas"
              list={listId}
              issue={issue("category")}
              hint="El asistente menciona hasta cuatro categorías."
            />
            <datalist id={listId}>
              {categorySuggestions.map((category) => (
                <option key={category} value={category} />
              ))}
            </datalist>
          </>
        ) : (
          <TextField label="Para quién es (opcional)" value={(draft as Plan).target ?? ""} onChange={(target) => onChange({ target: optionalText(target) })} />
        )}
      </div>

      <TextAreaField
        label="Descripción"
        value={draft.description ?? ""}
        onChange={(description) => onChange({ description: optionalText(description) })}
        rows={2}
        maxLength={TEXT_LIMITS.offeringDescription}
        hint="El asistente la usa para explicar este elemento."
        issue={issue("description")}
      />

      {catalog ? (
        <ItemPrices prices={(draft as CatalogItem).prices} onChange={(prices) => onChange({ prices } as Partial<CatalogItem>)} />
      ) : (
        <PlanPrices prices={(draft as Plan).prices} onChange={(prices) => onChange({ prices } as unknown as Partial<Plan & CatalogItem>)} />
      )}
      {pricesIssue && (
        <Alert tone="danger">
          <p>{pricesIssue.message}</p>
        </Alert>
      )}

      {catalog ? (
        <ListEditor
          label="Características relevantes"
          items={(draft as CatalogItem).features ?? []}
          onChange={(features) => onChange({ features: optionalList(features) })}
          placeholder="Ej.: Tamaño 12 oz"
          addLabel="Agregar característica"
        />
      ) : (
        <>
          <ListEditor
            label="Qué incluye"
            items={(draft as Plan).includes ?? []}
            onChange={(includes) => onChange({ includes })}
            placeholder="Ej.: Soporte por WhatsApp"
            addLabel="Agregar a lo que incluye"
          />
          <ListEditor
            label="Qué no incluye"
            items={(draft as Plan).not_included ?? []}
            onChange={(not_included) => onChange({ not_included })}
            placeholder="Ej.: Publicidad pagada"
            addLabel="Agregar a lo que no incluye"
            hint="Ayuda al asistente a no prometer de más."
          />
          {profiles.length > 1 && (
            <SelectField
              label="Perfil de pago"
              value={(draft as Plan).payment_profile ?? ""}
              options={[{ value: "", label: "Sin asignar" }, ...profiles.map((profile) => ({ value: profile, label: profile }))]}
              onChange={(profile) => onChange({ payment_profile: profile || null })}
              hint="Con qué datos de pago se cobra este plan."
            />
          )}
        </>
      )}

      <Toggle label="Disponible para la venta" description="Si lo desactivas, el asistente no lo ofrecerá." checked={draft.available !== false} onChange={(available) => onChange({ available })} />

      <div className="dialog__actions">
        <Button variant="ghost" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit">{isNew ? (catalog ? "Agregar producto a la lista" : "Agregar plan a la lista") : "Aplicar cambios"}</Button>
      </div>
      <p className="field__hint">Los cambios quedan en la lista; para conservarlos, usa «Guardar cambios» arriba.</p>
    </form>
  );
}

const PLAN_AMOUNTS: { key: keyof Omit<PlanPrice, "currency">; label: string; hint?: string }[] = [
  { key: "monthly", label: "Precio mensual" },
  { key: "price", label: "Precio de pago único" },
  { key: "annual", label: "Precio anual" },
  { key: "implementation", label: "Costo inicial", hint: "Instalación, implementación o inscripción." },
  { key: "first_payment", label: "Primer pago", hint: "Si es distinto de los siguientes." },
];

function PlanPrices({ prices, onChange }: { prices: PlanPrice[]; onChange: (prices: PlanPrice[]) => void }) {
  const replace = (index: number, patch: Partial<PlanPrice>) => onChange(prices.map((price, position) => (position === index ? { ...price, ...patch } : price)));
  return (
    <fieldset className="contract-group">
      <legend className="field__label">Precios</legend>
      {prices.map((price, index) => (
        <div className="subcard" key={index}>
          <div className="grid-2">
            <SelectField label="Moneda" value={price.currency} options={currencyOptions(price.currency)} onChange={(currency) => replace(index, { currency })} />
            {PLAN_AMOUNTS.map(({ key, label, hint }) => (
              <NumberField key={key} label={label} hint={hint} value={price[key] ?? null} onChange={(amount) => replace(index, { [key]: amount })} />
            ))}
          </div>
          {prices.length > 1 && (
            <Button variant="ghost" size="small" onClick={() => onChange(prices.filter((_, position) => position !== index))}>
              Quitar este precio
            </Button>
          )}
        </div>
      ))}
      <div>
        <Button variant="secondary" size="small" onClick={() => onChange([...prices, { currency: prices.some((price) => price.currency === "USD") ? DEFAULT_CURRENCY : "USD" }])}>
          Agregar precio en otra moneda
        </Button>
      </div>
    </fieldset>
  );
}

function ItemPrices({ prices, onChange }: { prices: ItemPrice[]; onChange: (prices: ItemPrice[]) => void }) {
  const replace = (index: number, patch: Partial<ItemPrice>) => onChange(prices.map((price, position) => (position === index ? { ...price, ...patch } : price)));
  return (
    <fieldset className="contract-group">
      <legend className="field__label">Precios</legend>
      {prices.map((price, index) => (
        <div className="grid-2" key={index}>
          <NumberField label="Precio" required value={price.amount || null} onChange={(amount) => replace(index, { amount: amount ?? 0 })} />
          <SelectField label="Moneda" value={price.currency} options={currencyOptions(price.currency)} onChange={(currency) => replace(index, { currency })} />
          {prices.length > 1 && (
            <div>
              <Button variant="ghost" size="small" onClick={() => onChange(prices.filter((_, position) => position !== index))}>
                Quitar este precio
              </Button>
            </div>
          )}
        </div>
      ))}
      <div>
        <Button variant="secondary" size="small" onClick={() => onChange([...prices, { currency: prices.some((price) => price.currency === "USD") ? DEFAULT_CURRENCY : "USD", amount: 0 }])}>
          Agregar precio en otra moneda
        </Button>
      </div>
    </fieldset>
  );
}
