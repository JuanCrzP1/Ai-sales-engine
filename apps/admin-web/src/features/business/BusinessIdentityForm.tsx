import { storedFieldHint } from "../../components/config/storedFieldHint";
import { TextAreaField, TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { WORD_LIMITS } from "../../domain/config/engineUsage";
import { useFieldIssue, useSection } from "../../state/useConfig";

export function BusinessIdentityForm() {
  const [business, update] = useSection("business");
  const nameIssue = useFieldIssue("business.name");
  const typeIssue = useFieldIssue("business.businessType");
  const valueIssue = useFieldIssue("business.valueProposition");

  return (
    <Card title="Datos del negocio">
      <div className="grid-2">
        <TextField
          label="Nombre comercial"
          required
          value={business.name}
          onChange={(name) => update({ name })}
          placeholder="Ej.: Panadería La Esquina"
          issue={nameIssue}
          hint={storedFieldHint("business.name", business.salesMode)}
        />
        <TextField
          label="¿A qué se dedica tu negocio?"
          required
          value={business.businessType}
          onChange={(businessType) => update({ businessType })}
          placeholder="Ej.: panadería artesanal con domicilios"
          wordLimit={WORD_LIMITS.businessType}
          issue={typeIssue}
          hint="Resúmelo en pocas palabras. Es lo primero que el asistente sabe de ti."
        />
      </div>
      <TextAreaField
        label="Descripción del negocio"
        value={business.description}
        onChange={(description) => update({ description })}
        placeholder="Qué haces, para quién y desde cuándo."
        hint={storedFieldHint("business.description", business.salesMode)}
      />
      <TextAreaField
        label="Propuesta de valor"
        required
        value={business.valueProposition}
        onChange={(valueProposition) => update({ valueProposition })}
        placeholder="Ej.: Pan recién horneado en tu puerta en menos de 30 minutos."
        wordLimit={WORD_LIMITS.valueProposition}
        issue={valueIssue}
        hint="Qué gana el cliente al comprarte. El asistente la usará como promesa comercial."
      />
    </Card>
  );
}
