import type { ReactNode } from "react";
import { ContractField } from "../components/config/ContractField";
import type { IconName } from "../components/ui/Icon";
import { SettingsCard, type CardTone } from "../components/ui/SettingsCard";
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
  icon?: IconName;
  tone?: CardTone;
  badge?: ReactNode;
  wide?: boolean;
  /** Plegada por defecto (opciones avanzadas). Con `false` se muestra abierta, como una tarjeta más. */
  collapsible?: boolean;
}

/**
 * Tarjeta con los campos del contrato que no tienen pantalla propia, generada desde el esquema que publica el servidor. Lo que contiene
 * se conserva aunque nadie la abra. Con un solo campo, la tarjeta ya lo nombra: el campo no repite su título.
 */
export function ContractSection({ title, description, section, fields, icon = "settings", tone = "slate", badge, wide = false, collapsible = true }: ContractSectionProps) {
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
            untitled={fields.length === 1}
            issueAt={issueAt}
            onChange={(next) => actions.setRootValue(section, { ...(value ?? {}), [name]: next })}
          />
        );
      })
    : (
      <ContractField root={schema} name={String(section)} node={sectionNode} value={value} path={String(section)} issueAt={issueAt} bare onChange={(next) => actions.setRootValue(section, next)} />
    );

  return (
    <SettingsCard icon={icon} tone={tone} title={title} description={description} badge={badge} wide={wide} collapsible={collapsible}>
      {content}
    </SettingsCard>
  );
}
