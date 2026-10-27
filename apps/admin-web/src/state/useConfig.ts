import { useCallback, useContext } from "react";
import type { EditableSection } from "../domain/config/operations";
import type { AssistantConfig } from "../domain/config/types";
import { issuesFor } from "../domain/validation/issues";
import { ConfigContext, type ConfigActions, type ConfigContextValue } from "./configContext";

export function useConfig(): ConfigContextValue {
  const context = useContext(ConfigContext);
  if (!context) throw new Error("useConfig debe usarse dentro de <ConfigProvider>.");
  return context;
}

export function useConfigActions(): ConfigActions {
  return useConfig().actions;
}

/** Valor de una sección y función para actualizarla parcialmente. */
export function useSection<K extends EditableSection>(section: K) {
  const { config, actions } = useConfig();
  const { updateSection } = actions;
  const update = useCallback((patch: Partial<AssistantConfig[K]>) => updateSection(section, patch), [updateSection, section]);
  return [config[section], update] as const;
}

/** Primer mensaje de error o advertencia de un campo, para mostrarlo junto al control. */
export function useFieldIssue(field: string) {
  const { issues } = useConfig();
  return issuesFor(issues, field)[0];
}
