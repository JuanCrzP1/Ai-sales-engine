import { useEffect, useState } from "react";
import { Button } from "../../components/ui/Button";
import { ChatPreview } from "../../components/ui/ChatPreview";
import { Badge } from "../../components/ui/Feedback";
import { SelectField, TextAreaField, TextField } from "../../components/ui/FormFields";
import { Icon } from "../../components/ui/Icon";
import { Card } from "../../components/ui/Layout";
import { Toggle } from "../../components/ui/Toggle";
import {
  MAX_FOLLOW_UP_STEPS,
  UNIT_LABELS,
  UNIT_MINUTES,
  durationText,
  nextStep,
  recommendedFollowUp,
  splitMinutes,
  stepProblem,
  type FollowUp,
  type FollowUpStep,
  type TimeUnit,
} from "../../domain/config/followUp";
import { useConfig, useFieldIssue, useSection } from "../../state/useConfig";

const UNITS = (Object.keys(UNIT_LABELS) as TimeUnit[]).map((unit) => ({ value: unit, label: UNIT_LABELS[unit] }));

/**
 * El seguimiento a quien deja de responder: viene armado con tres mensajes recomendados (con el trato y los emojis del negocio); el
 * dueño solo lo enciende y, si quiere, cambia los textos, los tiempos, el horario o agrega y quita mensajes.
 */
export function FollowUpForm() {
  const { document } = useConfig();
  const [messages, update] = useSection("messages");
  const groupIssue = useFieldIssue("messages.follow_up");
  const followUp: FollowUp = messages.follow_up ?? { enabled: false, business_hours_only: true, steps: [] };
  const steps = followUp.steps ?? [];
  const style = { formality: document.response_style?.formality, emojis: document.response_style?.emojis };
  const hasHours = Boolean(document.identity?.opening_hours?.length);

  const save = (change: Partial<FollowUp>) => update({ follow_up: { enabled: false, business_hours_only: true, ...followUp, ...change } });
  const setStep = (index: number, change: Partial<FollowUpStep>) => save({ steps: steps.map((step, at) => (at === index ? { ...step, ...change } : step)) });

  return (
    <Card
      icon="clock"
      tone="emerald"
      wide
      title="Seguimiento"
      description="Si un cliente deja de responder, le escribimos para retomar la conversación."
      badge={<Badge tone={followUp.enabled ? "success" : "neutral"}>{followUp.enabled ? "Encendido" : "Apagado"}</Badge>}
    >
      <Toggle
        label="Enviar seguimientos"
        description="Se detiene solo cuando el cliente responde, compra o avisa un pago, pide hablar con una persona, tu equipo lo atiende o dice que no le interesa."
        checked={Boolean(followUp.enabled)}
        onChange={(enabled) => save({ enabled, steps: enabled && steps.length === 0 ? recommendedFollowUp(style) : steps })}
      />
      {groupIssue && (
        <p className={`field__message field__message--${groupIssue.severity}`} role="alert">
          {groupIssue.message}
        </p>
      )}
      {followUp.enabled && (
        <div className="grid-2 follow-up">
          <div className="follow-up__steps">
            <Toggle
              label="Solo en el horario de mi negocio"
              description={
                hasHours
                  ? "Fuera de tu horario (Mi negocio) espera a que abras."
                  : "No tienes horario en Mi negocio: por ahora sale a cualquier hora."
              }
              checked={followUp.business_hours_only !== false}
              onChange={(business_hours_only) => save({ business_hours_only })}
            />
            <ol className="follow-up__list">
              {steps.map((step, index) => (
                <FollowUpStepEditor
                  key={index}
                  index={index}
                  step={step}
                  problem={stepProblem(steps, index)}
                  onChange={(change) => setStep(index, change)}
                  onRemove={steps.length > 1 ? () => save({ steps: steps.filter((_, at) => at !== index) }) : undefined}
                />
              ))}
            </ol>
            <div className="button-row">
              {steps.length < MAX_FOLLOW_UP_STEPS && (
                <Button variant="secondary" size="small" onClick={() => save({ steps: [...steps, nextStep(steps)] })}>
                  <Icon name="plus" size={14} /> Agregar mensaje
                </Button>
              )}
              <Button variant="ghost" size="small" onClick={() => save({ steps: recommendedFollowUp(style) })}>
                Usar los recomendados
              </Button>
            </div>
          </div>
          <ChatPreview
            caption="Vista previa: si el cliente deja de responder"
            lines={[
              { from: "customer", text: "¿Cuánto cuesta?" },
              { from: "assistant", text: "Te cuento: …" },
              ...steps.map((step) => ({ from: "assistant" as const, text: `${durationText(step.after_minutes)} después: ${step.message.trim() || "…"}` })),
            ]}
          />
        </div>
      )}
    </Card>
  );
}

function FollowUpStepEditor({
  index,
  step,
  problem,
  onChange,
  onRemove,
}: {
  index: number;
  step: FollowUpStep;
  problem: string | null;
  onChange: (change: Partial<FollowUpStep>) => void;
  onRemove?: () => void;
}) {
  // La unidad y el número se recuerdan mientras se escribe: al borrar el número, la unidad elegida no cambia sola.
  const [draft, setDraft] = useState(() => {
    const split = splitMinutes(step.after_minutes);
    return { text: String(split.amount), unit: split.unit };
  });
  const minutesOf = (text: string, unit: TimeUnit) => (Number(text.replace(/\D/g, "")) || 0) * UNIT_MINUTES[unit];
  // Si el tiempo cambió por fuera (los recomendados), se vuelve a mostrar en su unidad.
  useEffect(() => {
    if (minutesOf(draft.text, draft.unit) !== step.after_minutes) {
      const split = splitMinutes(step.after_minutes);
      setDraft({ text: String(split.amount), unit: split.unit });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step.after_minutes]);
  const change = (text: string, unit: TimeUnit) => {
    setDraft({ text: text.replace(/\D/g, ""), unit });
    onChange({ after_minutes: minutesOf(text, unit) });
  };
  const issue = useFieldIssue(`messages.follow_up.steps.${index}.message`);
  const timeIssue = useFieldIssue(`messages.follow_up.steps.${index}.after_minutes`);
  return (
    <li className="follow-up__step">
      <div className="follow-up__step-head">
        <strong>Mensaje {index + 1}</strong>
        {onRemove && (
          <Button variant="ghost" size="small" onClick={onRemove} aria-label={`Quitar el mensaje ${index + 1}`}>
            <Icon name="trash" size={14} /> Quitar
          </Button>
        )}
      </div>
      <div className="follow-up__when">
        <TextField
          label="Sale después de"
          inputMode="numeric"
          value={draft.text}
          onChange={(text) => change(text, draft.unit)}
          error={problem ?? timeIssue?.message}
        />
        <SelectField label="Unidad" value={draft.unit} options={UNITS} onChange={(unit) => change(draft.text, unit)} />
      </div>
      <TextAreaField
        label="Mensaje"
        required
        rows={3}
        value={step.message}
        onChange={(message) => onChange({ message })}
        placeholder="Ej.: ¿Pudiste ver la información?"
        issue={issue}
        error={step.message.trim() ? undefined : "Escribe el mensaje."}
      />
    </li>
  );
}
