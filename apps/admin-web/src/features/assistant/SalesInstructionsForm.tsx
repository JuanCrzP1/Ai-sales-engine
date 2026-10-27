import { storedFieldHint } from "../../components/config/storedFieldHint";
import { Card } from "../../components/ui/Layout";
import { ListEditor } from "../../components/ui/ListEditor";
import { useConfig, useSection } from "../../state/useConfig";

export function SalesInstructionsForm() {
  const [behavior, update] = useSection("behavior");
  const { config } = useConfig();
  const salesMode = config.business.salesMode;

  return (
    <Card title="Instrucciones de venta" description="Reglas comerciales y preguntas que el asistente debería hacer.">
      <ListEditor
        label="Reglas comerciales"
        hint={storedFieldHint("behavior.salesRules", salesMode)}
        items={behavior.salesRules}
        onChange={(salesRules) => update({ salesRules })}
        placeholder="Ej.: confirmar la dirección antes de cerrar el pedido"
        addLabel="Agregar regla"
        emptyText="Sin reglas por ahora."
      />
      <ListEditor
        label="Preguntas que el asistente debe hacer"
        hint={storedFieldHint("behavior.discoveryQuestions", salesMode)}
        items={behavior.discoveryQuestions}
        onChange={(discoveryQuestions) => update({ discoveryQuestions })}
        placeholder="Ej.: ¿Para cuántas personas es el pedido?"
        addLabel="Agregar pregunta"
        emptyText="Sin preguntas por ahora."
      />
    </Card>
  );
}
