import { storedFieldHint } from "../../components/config/storedFieldHint";
import { Alert } from "../../components/ui/Feedback";
import { TextAreaField, TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { ListEditor } from "../../components/ui/ListEditor";
import { MAX_PROBLEMS_USED } from "../../domain/config/engineUsage";
import { useConfig, useFieldIssue, useSection } from "../../state/useConfig";

/** Lo que el asistente debe saber del cliente ideal para recomendar mejor. */
export function SalesKnowledgeForm() {
  const [behavior, update] = useSection("behavior");
  const { config } = useConfig();
  const problemsIssue = useFieldIssue("behavior.customerProblems");

  return (
    <Card title="Lo que debe tener en cuenta al recomendar" description="Ayuda al asistente a entender por qué te compran.">
      {problemsIssue && <Alert tone="warning">{problemsIssue.message}</Alert>}
      <div className="grid-2">
        <TextField
          label="Principal razón por la que te compran"
          value={behavior.primaryMotivation}
          onChange={(primaryMotivation) => update({ primaryMotivation })}
          placeholder="Ej.: ahorrar tiempo"
        />
        <TextField
          label="Segunda razón (opcional)"
          value={behavior.secondaryMotivation}
          onChange={(secondaryMotivation) => update({ secondaryMotivation })}
          placeholder="Ej.: ahorrar dinero"
        />
      </div>
      <ListEditor
        label="Problemas de tus clientes que resuelves"
        hint={`Escribe primero los más importantes: el asistente usa los ${MAX_PROBLEMS_USED} primeros.`}
        items={behavior.customerProblems}
        onChange={(customerProblems) => update({ customerProblems })}
        placeholder="Ej.: pierden pedidos porque no alcanzan a responder"
        addLabel="Agregar problema"
      />
      <TextAreaField
        label="Notas para recomendar productos o servicios"
        value={behavior.recommendationNotes}
        onChange={(recommendationNotes) => update({ recommendationNotes })}
        placeholder="Ej.: si piden café, sugerir un acompañamiento de panadería."
        hint={storedFieldHint("behavior.recommendationNotes", config.business.salesMode)}
      />
    </Card>
  );
}
