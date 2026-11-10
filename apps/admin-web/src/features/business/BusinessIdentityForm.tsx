import { TextAreaField, TextField } from "../../components/ui/FormFields";
import { SettingsCard } from "../../components/ui/SettingsCard";
import { optionalText } from "../../domain/config/document";
import { TEXT_LIMITS } from "../../domain/config/engineLimits";
import { useFieldIssue, useSection } from "../../state/useConfig";

/** Quién es el negocio: su nombre, su marca y a qué se dedica. */
export function BusinessIdentityForm() {
  const [identity, update] = useSection("identity");
  const nameIssue = useFieldIssue("identity.name");
  const brandIssue = useFieldIssue("identity.brand_name");
  const industryIssue = useFieldIssue("identity.industry");

  return (
    <SettingsCard icon="store" tone="indigo" title="Datos del negocio" description="Cómo se llama y a qué se dedica.">
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
        maxLength={TEXT_LIMITS.businessType}
        issue={industryIssue}
        hint="Resúmelo en pocas palabras. Es lo primero que el asistente sabe de ti."
      />
    </SettingsCard>
  );
}

/** Qué hace el negocio y qué promete: lo que el asistente cuenta cuando le preguntan. */
export function BusinessPromiseForm() {
  const [identity, update] = useSection("identity");
  const descriptionIssue = useFieldIssue("identity.description");
  const valueIssue = useFieldIssue("identity.value_proposition");

  return (
    <SettingsCard icon="sparkles" tone="violet" title="Qué haces y qué prometes" description="Escríbelo como se lo explicarías a un cliente nuevo." wide>
      <TextAreaField
        label="Descripción del negocio"
        required
        value={identity.description}
        onChange={(description) => update({ description })}
        placeholder="Qué haces, para quién y desde cuándo."
        maxLength={TEXT_LIMITS.description}
        issue={descriptionIssue}
      />
      <TextAreaField
        label="Propuesta de valor"
        required
        value={identity.value_proposition}
        onChange={(value_proposition) => update({ value_proposition })}
        placeholder="Ej.: Pan recién horneado en tu puerta en menos de 30 minutos."
        maxLength={TEXT_LIMITS.valueProposition}
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
    </SettingsCard>
  );
}
