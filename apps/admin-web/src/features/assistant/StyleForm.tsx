import { storedFieldHint } from "../../components/config/storedFieldHint";
import { RadioGroup } from "../../components/ui/ChoiceGroup";
import { Card } from "../../components/ui/Layout";
import { RESPONSE_LENGTHS, TONES } from "../../domain/config/options";
import { useConfig, useSection } from "../../state/useConfig";

export function StyleForm() {
  const [behavior, update] = useSection("behavior");
  const { config } = useConfig();

  return (
    <Card title="Estilo de atención">
      <RadioGroup
        legend="Tono de comunicación"
        name="tone"
        options={TONES}
        value={behavior.tone}
        onChange={(tone) => update({ tone })}
        hint={storedFieldHint("behavior.tone", config.business.salesMode)}
      />
      <RadioGroup
        legend="Largo de las respuestas"
        name="response-length"
        options={RESPONSE_LENGTHS}
        value={behavior.responseLength}
        onChange={(responseLength) => update({ responseLength })}
      />
    </Card>
  );
}
