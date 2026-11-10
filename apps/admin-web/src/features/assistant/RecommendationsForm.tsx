import { Button } from "../../components/ui/Button";
import { SelectField, TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import type { RecommendationRule } from "../../domain/config/types";
import { optionalList, offerEntries } from "../../domain/config/document";
import { MAX_PROFILE_ITEMS } from "../../domain/config/engineLimits";
import { useConfig, useFieldIssue, useSection } from "../../state/useConfig";

/** Qué recomendar en cada situación del cliente. */
export function RecommendationsForm() {
  const { document } = useConfig();
  const [sales, update] = useSection("sales");
  const rules = sales.recommendation_rules ?? [];
  const entries = offerEntries(document);
  const set = (next: RecommendationRule[]) => update({ recommendation_rules: optionalList(next) });
  const known = new Set(entries.map((entry) => entry.id));
  const options = [{ value: "", label: "Elige qué recomendar" }, ...entries.map((entry) => ({ value: entry.id, label: entry.name || entry.id }))];

  return (
    <Card icon="target" tone="sky" title="Recomendaciones" description="Qué plan o producto debe sugerir el asistente según la situación del cliente.">
      {rules.length === 0 && <p className="field__hint">Aún no hay recomendaciones.</p>}
      {rules.map((rule, index) => (
        <RuleRow
          key={index}
          rule={rule}
          index={index}
          options={rule.recommend && !known.has(rule.recommend) ? [...options, { value: rule.recommend, label: rule.recommend }] : options}
          onChange={(patch) => set(rules.map((item, position) => (position === index ? { ...item, ...patch } : item)))}
          onRemove={() => set(rules.filter((_, position) => position !== index))}
        />
      ))}
      <div>
        <Button variant="secondary" disabled={rules.length >= MAX_PROFILE_ITEMS} onClick={() => set([...rules, { when: "", recommend: "" }])}>
          Agregar recomendación
        </Button>
      </div>
    </Card>
  );
}

interface RuleRowProps {
  rule: RecommendationRule;
  index: number;
  options: { value: string; label: string }[];
  onChange: (patch: Partial<RecommendationRule>) => void;
  onRemove: () => void;
}

function RuleRow({ rule, index, options, onChange, onRemove }: RuleRowProps) {
  const whenIssue = useFieldIssue(`sales.recommendation_rules.${index}.when`);
  const recommendIssue = useFieldIssue(`sales.recommendation_rules.${index}.recommend`);
  return (
    <fieldset className="subcard">
      <legend className="visually-hidden">Recomendación {index + 1}</legend>
      <div className="grid-2">
        <TextField label="Situación del cliente" value={rule.when} onChange={(when) => onChange({ when })} placeholder="Ej.: Tiene poco presupuesto" issue={whenIssue} />
        <SelectField label="Recomendar" value={rule.recommend} options={options} onChange={(recommend) => onChange({ recommend })} issue={recommendIssue} />
      </div>
      <div>
        <Button variant="danger" size="small" onClick={onRemove} aria-label={`Quitar la recomendación ${index + 1}`}>
          Quitar
        </Button>
      </div>
    </fieldset>
  );
}
