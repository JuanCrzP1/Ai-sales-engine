import { RadioGroup } from "../../components/ui/ChoiceGroup";
import { NumberField, SelectField, TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { ListEditor } from "../../components/ui/ListEditor";
import { optionalList, optionalText } from "../../domain/config/document";
import { EMOJI_OPTIONS, FORMALITY_OPTIONS, RESPONSE_LENGTHS } from "../../domain/config/options";
import { useFieldIssue, useSection } from "../../state/useConfig";

/** Personalidad y estilo de atención. El largo de las respuestas fija el límite de palabras que aplica el motor. */
export function StyleForm() {
  const [style, update] = useSection("response_style");
  const toneIssue = useFieldIssue("response_style.tone");
  const voiceIssue = useFieldIssue("response_style.voice");
  const maxWordsIssue = useFieldIssue("response_style.max_words");
  const instructionsIssue = useFieldIssue("response_style.instructions");

  return (
    <Card title="Personalidad y estilo de atención">
      <div className="grid-2">
        <TextField label="Tono de comunicación" value={style.tone ?? ""} onChange={(tone) => update({ tone: optionalText(tone) })} placeholder="Ej.: cercano y claro" issue={toneIssue} />
        <TextField label="Personalidad de la marca" value={style.voice ?? ""} onChange={(voice) => update({ voice: optionalText(voice) })} placeholder="Ej.: experta pero sencilla" issue={voiceIssue} />
        <SelectField label="Trato al cliente" value={style.formality ?? ""} options={FORMALITY_OPTIONS} onChange={(formality) => update({ formality: formality || null })} />
        <SelectField
          label="¿Puede usar emojis?"
          value={style.emojis === true ? "yes" : style.emojis === false ? "no" : ""}
          options={EMOJI_OPTIONS}
          onChange={(choice) => update({ emojis: choice === "" ? null : choice === "yes" })}
        />
      </div>
      <RadioGroup legend="Largo de las respuestas" name="response-length" options={RESPONSE_LENGTHS} value={style.length ?? "short"} onChange={(length) => update({ length })} />
      <NumberField
        label="Límite de palabras (opcional)"
        value={style.max_words ?? null}
        onChange={(max_words) => update({ max_words })}
        issue={maxWordsIssue}
        hint="Ajuste avanzado dentro del rango de la opción elegida. Si lo dejas vacío, se usa el de la opción."
      />
      <ListEditor
        label="Cómo debe expresarse"
        items={style.instructions ?? []}
        onChange={(instructions) => update({ instructions: optionalList(instructions) })}
        placeholder="Ej.: No uses tecnicismos"
        addLabel="Agregar indicación"
      />
      {instructionsIssue && <p className={`field__message field__message--${instructionsIssue.severity}`}>{instructionsIssue.message}</p>}
    </Card>
  );
}
