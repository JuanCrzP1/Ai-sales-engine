import { RadioGroup } from "../../components/ui/ChoiceGroup";
import { TextAreaField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { ListEditor } from "../../components/ui/ListEditor";
import { Toggle } from "../../components/ui/Toggle";
import { escalationOf, MAX_ESCALATION_INSTRUCTIONS_CHARS, MAX_ESCALATION_TOPICS, ON_REQUEST_OPTIONS } from "../../domain/assistant/escalation";
import { optionalText } from "../../domain/config/document";
import { useConfig, useFieldIssue, useSection } from "../../state/useConfig";

/**
 * Cuándo pasa el asistente el chat a una persona del equipo. Son instrucciones para la IA: decide ella con lo que dice el cliente,
 * no con palabras sueltas. Reclamos y pagos avisados siempre pasan al equipo; el horario y lo que pasa después del traspaso están en
 * Configuración → Atención humana.
 */
export function EscalationForm() {
  const { document } = useConfig();
  const [, update] = useSection("escalation");
  const rules = escalationOf(document);
  const alwaysIssue = useFieldIssue("escalation.always_topics");
  const neverIssue = useFieldIssue("escalation.never_topics");
  const instructionsIssue = useFieldIssue("escalation.instructions");
  const full = (topics: string[]) => (topics.length >= MAX_ESCALATION_TOPICS ? `Llegaste al máximo de ${MAX_ESCALATION_TOPICS} temas.` : undefined);

  return (
    <Card
      icon="users"
      tone="amber"
      title="Cuándo pasar a una persona"
      description="Cuándo el asistente le pasa el chat a tu equipo. Si el cliente reclama o avisa que ya pagó, siempre lo pasa."
    >
      <RadioGroup
        legend="Si el cliente pide hablar con una persona"
        name="escalation-on-request"
        options={ON_REQUEST_OPTIONS}
        value={rules.on_request}
        onChange={(on_request) => update({ on_request })}
      />
      <ListEditor
        label="Temas que siempre atiende tu equipo"
        hint={full(rules.always_topics) ?? "Si el cliente pregunta por uno de estos temas, el asistente le pasa el chat a tu equipo."}
        items={rules.always_topics}
        onChange={(always_topics) => update({ always_topics: always_topics.slice(0, MAX_ESCALATION_TOPICS) })}
        placeholder="Ej.: reembolsos"
        addLabel="Agregar tema"
        emptyText="Ninguno: el asistente responde todos los temas."
      />
      {alwaysIssue && <p className={`field__message field__message--${alwaysIssue.severity}`}>{alwaysIssue.message}</p>}
      <ListEditor
        label="Temas que resuelve el asistente"
        hint={full(rules.never_topics) ?? "Los responde él mismo con la información de tu negocio, salvo que el cliente pida una persona."}
        items={rules.never_topics}
        onChange={(never_topics) => update({ never_topics: never_topics.slice(0, MAX_ESCALATION_TOPICS) })}
        placeholder="Ej.: precios y horarios"
        addLabel="Agregar tema"
      />
      {neverIssue && <p className={`field__message field__message--${neverIssue.severity}`}>{neverIssue.message}</p>}
      <Toggle
        label="Pasar el chat si la conversación se estanca"
        description="Si el cliente repite lo mismo o se nota frustrado y el asistente no logra ayudarlo."
        checked={rules.when_stuck}
        onChange={(when_stuck) => update({ when_stuck })}
      />
      <TextAreaField
        label="Otras indicaciones (opcional)"
        value={rules.instructions ?? ""}
        onChange={(instructions) => update({ instructions: optionalText(instructions) })}
        placeholder="Ej.: Los fines de semana avisa que el equipo responde el lunes."
        maxLength={MAX_ESCALATION_INSTRUCTIONS_CHARS}
        issue={instructionsIssue}
      />
    </Card>
  );
}
