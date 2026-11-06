import { TextAreaField, TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { optionalText } from "../../domain/config/document";
import { WORD_LIMITS } from "../../domain/config/engineLimits";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function BusinessIdentityForm() {
  const [identity, update] = useSection("identity");
  const nameIssue = useFieldIssue("identity.name");
  const brandIssue = useFieldIssue("identity.brand_name");
  const industryIssue = useFieldIssue("identity.industry");
  const descriptionIssue = useFieldIssue("identity.description");
  const valueIssue = useFieldIssue("identity.value_proposition");

  return (
    <Card title="Datos del negocio">
      <div className="grid-2">
        <TextField label="Nombre comercial" required value={identity.name} onChange={(name) => update({ name })} placeholder="Ej.: Panadería La Esquina" issue={nameIssue} />
        <TextField
          label="Marca (opcional)"
          value={identity.brand_name ?? ""}
          onChange={(brand) => update({ brand_name: optionalText(brand) })}
          issue={brandIssue}
          hint="Con este nombre se presenta el asistente, si es distinto del comercial."
        />
      </div>
      <TextField
        label="¿A qué se dedica tu negocio?"
        required
        value={identity.industry}
        onChange={(industry) => update({ industry })}
        placeholder="Ej.: panadería artesanal con domicilios"
        wordLimit={WORD_LIMITS.businessType}
        issue={industryIssue}
        hint="Resúmelo en pocas palabras. Es lo primero que el asistente sabe de ti."
      />
      <TextAreaField
        label="Descripción del negocio"
        required
        value={identity.description}
        onChange={(description) => update({ description })}
        placeholder="Qué haces, para quién y desde cuándo."
        wordLimit={WORD_LIMITS.description}
        issue={descriptionIssue}
      />
      <TextAreaField
        label="Propuesta de valor"
        required
        value={identity.value_proposition}
        onChange={(value_proposition) => update({ value_proposition })}
        placeholder="Ej.: Pan recién horneado en tu puerta en menos de 30 minutos."
        wordLimit={WORD_LIMITS.valueProposition}
        issue={valueIssue}
        hint="Qué gana el cliente al comprarte. El asistente la usará como promesa comercial."
      />
      <TextAreaField
        label="Posicionamiento (opcional)"
        value={identity.positioning ?? ""}
        onChange={(positioning) => update({ positioning: optionalText(positioning) })}
        rows={2}
        hint="A quién te diriges y qué problema resuelves."
      />
    </Card>
  );
}
