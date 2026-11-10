import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { ListEditor } from "../../components/ui/ListEditor";
import type { CustomerProblem } from "../../domain/config/types";
import { optionalList, optionalText } from "../../domain/config/document";
import { MAX_CUSTOMER_PROBLEMS } from "../../domain/config/engineLimits";
import { createId } from "../../lib/ids";
import { useFieldIssue, useSection } from "../../state/useConfig";

/** Lo que el asistente debe saber para recomendar y vender: motivos, problemas, argumentos e instrucciones del negocio. */
export function SalesKnowledgeForm() {
  const [sales, update] = useSection("sales");
  const problemsIssue = useFieldIssue("sales.customer_problems");
  const primaryIssue = useFieldIssue("sales.buying_motivation.primary");
  const instructionsIssue = useFieldIssue("sales.instructions");
  const motivation = sales.buying_motivation;

  const changeMotivation = (primary: string, secondary: string | null | undefined) => {
    update({ buying_motivation: primary.trim() || secondary ? { primary, secondary: secondary ?? null } : null });
  };

  return (
    <Card icon="lightbulb" tone="amber" title="Instrucciones comerciales" description="Ayuda al asistente a entender por qué te compran y cómo debe vender.">
      {problemsIssue && <Alert tone="warning">{problemsIssue.message}</Alert>}
      <div className="grid-2">
        <TextField
          label="Principal razón por la que te compran"
          value={motivation?.primary ?? ""}
          onChange={(primary) => changeMotivation(primary, motivation?.secondary)}
          placeholder="Ej.: ahorrar tiempo"
          issue={primaryIssue}
        />
        <TextField
          label="Segunda razón (opcional)"
          value={motivation?.secondary ?? ""}
          onChange={(secondary) => changeMotivation(motivation?.primary ?? "", optionalText(secondary))}
          placeholder="Ej.: ahorrar dinero"
        />
      </div>

      <ProblemsEditor problems={sales.customer_problems ?? []} onChange={(problems) => update({ customer_problems: optionalList(problems) })} />

      <ListEditor
        label="Cómo debe vender en este negocio"
        items={sales.instructions ?? []}
        onChange={(instructions) => update({ instructions: optionalList(instructions) })}
        placeholder="Ej.: Pregunta el presupuesto antes de recomendar"
        addLabel="Agregar instrucción"
        hint="Indicaciones particulares de tu negocio."
      />
      {instructionsIssue && <p className={`field__message field__message--${instructionsIssue.severity}`}>{instructionsIssue.message}</p>}
      <ListEditor label="Resultados que obtiene el cliente" items={sales.benefits ?? []} onChange={(benefits) => update({ benefits: optionalList(benefits) })} placeholder="Ej.: Más ventas sin contratar personal" addLabel="Agregar beneficio" />
      <ListEditor label="Argumentos de venta" items={sales.arguments ?? []} onChange={(items) => update({ arguments: optionalList(items) })} placeholder="Ej.: Sin contratos de permanencia" addLabel="Agregar argumento" />
      <ListEditor
        label="Preguntas para entender al cliente"
        items={sales.discovery?.questions ?? []}
        onChange={(questions) => update({ discovery: { ...sales.discovery, questions: optionalList(questions) } })}
        placeholder="Ej.: ¿Cuántos clientes atiendes al mes?"
        addLabel="Agregar pregunta"
      />
    </Card>
  );
}

/**
 * Cada fila es un problema con su primer impacto. El resto de sus datos (señales, urgencia...) se conserva y se edita en
 * la estrategia avanzada.
 */
function ProblemsEditor({ problems, onChange }: { problems: CustomerProblem[]; onChange: (problems: CustomerProblem[]) => void }) {
  const change = (index: number, text: string) =>
    onChange(problems.map((problem, position) => (position === index ? { ...problem, impacts: [text, ...(problem.impacts ?? []).slice(1)] } : problem)));

  return (
    <fieldset className="contract-group">
      <legend className="field__label">Problemas de tus clientes que resuelves</legend>
      <p className="field__hint">Hasta {MAX_CUSTOMER_PROBLEMS}. El asistente los usa todos para entender a tus clientes.</p>
      {problems.map((problem, index) => (
        <div className="list-editor__row" key={problem.id}>
          <input
            className="input"
            aria-label={`Problema ${index + 1}`}
            value={problem.impacts?.[0] ?? ""}
            placeholder={problem.id}
            onChange={(event) => change(index, event.target.value)}
          />
          <Button variant="danger" size="small" onClick={() => onChange(problems.filter((_, position) => position !== index))} aria-label={`Quitar el problema ${index + 1}`}>
            Quitar
          </Button>
        </div>
      ))}
      <div>
        <Button
          variant="secondary"
          size="small"
          disabled={problems.length >= MAX_CUSTOMER_PROBLEMS}
          onClick={() => onChange([...problems, { id: createId("problema"), impacts: [""] }])}
        >
          Agregar problema
        </Button>
      </div>
    </fieldset>
  );
}
