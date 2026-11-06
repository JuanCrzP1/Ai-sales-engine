import { ContractField } from "../components/config/ContractField";
import { Disclosure } from "../components/ui/Disclosure";
import { fieldShape, nodeAt } from "../domain/config/contractSchema";
import type { BusinessDocument } from "../domain/config/types";
import { issuesFor } from "../domain/validation/issues";
import { useContractSchema } from "../state/directoryContext";
import { useConfig } from "../state/useConfig";

interface ContractSectionProps {
  title: string;
  description?: string;
  /** Sección del documento. */
  section: keyof BusinessDocument;
  /** Campos de la sección que se muestran; sin indicar, la sección completa. */
  fields?: string[];
}

/**
 * Formulario de los campos del contrato que no tienen pantalla propia, generado desde el esquema que publica el servidor.
 * Plegado por defecto: son opciones avanzadas, y lo que contienen se conserva aunque nadie lo abra.
 */
export function ContractSection({ title, description, section, fields, ...props }: ContractSectionProps) {
  const schema = useContractSchema();
  const { document, issues, actions } = useConfig();
  const sectionNode = nodeAt(schema, [section]);
  const value = document[section] as Record<string, unknown> | null | undefined;
  const issueAt = (path: string) => issuesFor(issues, path)[0];

  const content = fields
    ? fields.map((name) => {
        const node = fieldShape(schema, sectionNode).node.properties?.[name];
        if (!node) throw new Error(`El contrato no define ${String(section)}.${name}.`);
        return (
          <ContractField
            key={name}
            root={schema}
            name={name}
            node={node}
            value={value?.[name]}
            path={`${String(section)}.${name}`}
            issueAt={issueAt}
            onChange={(next) => actions.setRootValue(section, { ...(value ?? {}), [name]: next })}
          />
        );
      })
    : (
      <ContractField root={schema} name={String(section)} node={sectionNode} value={value} path={String(section)} issueAt={issueAt} bare onChange={(next) => actions.setRootValue(section, next)} />
    );

  return (
    <Disclosure title={title} description={description} {...props}>
      {content}
    </Disclosure>
  );
}
