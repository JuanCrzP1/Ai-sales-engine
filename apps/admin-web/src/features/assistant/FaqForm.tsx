import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert } from "../../components/ui/Feedback";
import { TextAreaField, TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import type { Faq } from "../../domain/config/types";
import { MAX_FAQ_ANSWER_CHARS, MAX_FAQ_QUESTION_CHARS, MAX_FAQS } from "../../domain/config/engineLimits";
import { useFieldIssue, useSection } from "../../state/useConfig";

/** Preguntas frecuentes que el asistente consulta para responder sin inventar. */
export function FaqForm() {
  const [knowledge, update] = useSection("knowledge");
  const listIssue = useFieldIssue("knowledge.faqs");
  const groupIssue = useFieldIssue("knowledge");
  const faqs = knowledge.faqs ?? [];
  const issue = listIssue ?? groupIssue;

  return (
    <Card icon="question" tone="indigo" title="Preguntas frecuentes" description="El asistente usa estas respuestas tal como las escribas.">
      {issue && <Alert tone={issue.severity === "error" ? "danger" : "warning"}>{issue.message}</Alert>}
      {faqs.length === 0 && <p className="field__hint">Aún no hay preguntas frecuentes.</p>}
      {faqs.map((faq, index) => (
        <FaqRow
          key={index}
          faq={faq}
          index={index}
          onChange={(patch) => update({ faqs: faqs.map((item, position) => (position === index ? { ...item, ...patch } : item)) })}
          onRemove={() => update({ faqs: faqs.filter((_, position) => position !== index) })}
        />
      ))}
      <div>
        <Button variant="secondary" onClick={() => update({ faqs: [...faqs, { question: "", answer: "" }] })} disabled={faqs.length >= MAX_FAQS}>
          Agregar pregunta frecuente
        </Button>
      </div>
    </Card>
  );
}

interface FaqRowProps {
  faq: Faq;
  index: number;
  onChange: (patch: Partial<Faq>) => void;
  onRemove: () => void;
}

function FaqRow({ faq, index, onChange, onRemove }: FaqRowProps) {
  const questionIssue = useFieldIssue(`knowledge.faqs.${index}.question`);
  const answerIssue = useFieldIssue(`knowledge.faqs.${index}.answer`);
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
      <ConfirmButton confirmLabel="Sí, quitar" onConfirm={onRemove}>
        Quitar pregunta {index + 1}
      </ConfirmButton>
    </fieldset>
  );
}
