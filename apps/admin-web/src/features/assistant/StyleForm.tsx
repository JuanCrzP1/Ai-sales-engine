import { RadioGroup } from "../../components/ui/ChoiceGroup";
import { Card } from "../../components/ui/Layout";
import { RESPONSE_LENGTHS } from "../../domain/config/options";
import { useSection } from "../../state/useConfig";

/** Largo de las respuestas: cada opción fija el límite de palabras que aplica el motor. */
export function StyleForm() {
  const [behavior, update] = useSection("behavior");

  return (
    <Card title="Estilo de atención">
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
