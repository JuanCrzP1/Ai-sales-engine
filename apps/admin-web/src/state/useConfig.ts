import { useCallback, useContext } from "react";
import type { BusinessDocument, EditableSection } from "../domain/config/types";
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

/** Valor de una sección del documento y función para actualizarla parcialmente. */
export function useSection<K extends EditableSection>(section: K) {
  const { document, actions } = useConfig();
  const { updateSection } = actions;
  const update = useCallback((patch: Partial<BusinessDocument[K]>) => updateSection(section, patch), [updateSection, section]);
  return [document[section], update] as const;
}

/** Primer mensaje de error o advertencia de un campo del documento, para mostrarlo junto al control. */
export function useFieldIssue(field: string) {
  const { issues } = useConfig();
  return issuesFor(issues, field)[0];
}
