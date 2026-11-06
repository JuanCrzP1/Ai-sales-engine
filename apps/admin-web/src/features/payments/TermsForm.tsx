import { TextAreaField, TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { ListEditor } from "../../components/ui/ListEditor";
import type { Policies } from "../../domain/config/types";
import { optionalList, optionalText } from "../../domain/config/document";
import { useFieldIssue, useSection } from "../../state/useConfig";

/** Condiciones comerciales y políticas oficiales, que el asistente comunica tal cual cuando se las preguntan. */
export function TermsForm() {
  const [terms, update] = useSection("terms");
  const policies = terms.policies ?? {};
  const noteIssue = useFieldIssue("terms.price_note");
  const warrantyIssue = useFieldIssue("terms.policies.warranty");
  const returnsIssue = useFieldIssue("terms.policies.returns");
  const cancellationIssue = useFieldIssue("terms.policies.cancellation");

  const changePolicy = (key: keyof Policies, text: string) => {
    const next = { ...policies, [key]: optionalText(text) };
    update({ policies: Object.values(next).some(Boolean) ? next : null });
  };

  return (
    <Card title="Condiciones y políticas" description="Lo que el asistente debe respetar al hablar de precios y lo que responde si le preguntan por garantías o devoluciones.">
      <ListEditor
        label="Condiciones de compra"
        items={terms.conditions ?? []}
        onChange={(conditions) => update({ conditions: optionalList(conditions) })}
        placeholder="Ej.: Domicilio gratis en compras superiores a $50.000"
        addLabel="Agregar condición"
        emptyText="Sin condiciones por ahora."
      />
      <TextField
        label="Aclaración sobre el precio (opcional)"
        value={terms.price_note ?? ""}
        onChange={(note) => update({ price_note: optionalText(note) })}
        issue={noteIssue}
        placeholder="Ej.: El precio final se confirma al cotizar."
      />
      <TextAreaField label="Garantía" value={policies.warranty ?? ""} onChange={(text) => changePolicy("warranty", text)} rows={2} issue={warrantyIssue} hint="Qué cubre y por cuánto tiempo." />
      <TextAreaField label="Cambios y devoluciones" value={policies.returns ?? ""} onChange={(text) => changePolicy("returns", text)} rows={2} issue={returnsIssue} />
      <TextAreaField
        label="Cancelaciones y reembolsos"
        value={policies.cancellation ?? ""}
        onChange={(text) => changePolicy("cancellation", text)}
        rows={2}
        issue={cancellationIssue}
        hint="Citas, reservas o suscripciones."
      />
    </Card>
  );
}
