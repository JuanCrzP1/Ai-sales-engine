import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { TextAreaField, TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { MAX_FAQ_ANSWER_CHARS, MAX_FAQ_QUESTION_CHARS, MAX_FAQS } from "../../domain/config/engineLimits";
import { createFaq } from "../../domain/config/factories";
import type { FaqEntry } from "../../domain/config/types";
import { useFieldIssue, useSection } from "../../state/useConfig";

/** Preguntas frecuentes que el asistente consulta para responder sin inventar. */
export function FaqForm() {
  const [behavior, update] = useSection("behavior");
  const listIssue = useFieldIssue("behavior.faqs");
  const faqs = behavior.faqs;

  const change = (id: string, patch: Partial<FaqEntry>) => update({ faqs: faqs.map((faq) => (faq.id === id ? { ...faq, ...patch } : faq)) });
  const remove = (id: string) => update({ faqs: faqs.filter((faq) => faq.id !== id) });

  return (
    <Card
      title="Preguntas frecuentes"
      description="El asistente usa estas respuestas tal como las escribas. Si una pregunta no está aquí ni en tu configuración, dirá que no tiene ese dato."
    >
      {listIssue && <Alert tone={listIssue.severity === "error" ? "danger" : "warning"}>{listIssue.message}</Alert>}
      {faqs.length === 0 && <p className="field__hint">Aún no hay preguntas frecuentes.</p>}
      {faqs.map((faq, index) => (
        <FaqRow key={faq.id} faq={faq} index={index} onChange={(patch) => change(faq.id, patch)} onRemove={() => remove(faq.id)} />
      ))}
      <Button variant="secondary" onClick={() => update({ faqs: [...faqs, createFaq()] })} disabled={faqs.length >= MAX_FAQS}>
        Agregar pregunta
      </Button>
    </Card>
  );
}

interface FaqRowProps {
  faq: FaqEntry;
  index: number;
  onChange: (patch: Partial<FaqEntry>) => void;
  onRemove: () => void;
}

function FaqRow({ faq, index, onChange, onRemove }: FaqRowProps) {
  const questionIssue = useFieldIssue(`behavior.faqs.${faq.id}.question`);
  const answerIssue = useFieldIssue(`behavior.faqs.${faq.id}.answer`);
  return (
    <fieldset className="faq-entry">
      <legend className="field__label">Pregunta {index + 1}</legend>
      <TextField
        label="Pregunta"
        value={faq.question}
        onChange={(question) => onChange({ question })}
        placeholder="Ej.: ¿Hacen domicilios?"
        issue={questionIssue}
        hint={`Hasta ${MAX_FAQ_QUESTION_CHARS} caracteres.`}
      />
      <TextAreaField
        label="Respuesta"
        value={faq.answer}
        onChange={(answer) => onChange({ answer })}
        placeholder="Ej.: Sí, en el barrio y alrededores."
        issue={answerIssue}
        hint={`Hasta ${MAX_FAQ_ANSWER_CHARS} caracteres.`}
      />
      <Button variant="danger" size="small" onClick={onRemove} aria-label={`Quitar la pregunta ${index + 1}`}>
        Quitar
      </Button>
    </fieldset>
  );
}
