import { useCallback, useState } from "react";
import { createOffering } from "../../domain/config/factories";
import type { Offering } from "../../domain/config/types";
import { validateOffering } from "../../domain/validation/rules";
import type { ValidationIssue } from "../../domain/validation/types";
import { useConfig } from "../../state/useConfig";

interface EditorState {
  draft: Offering;
  isNew: boolean;
  issues: ValidationIssue[];
}

/** Borrador de un producto o servicio: se valida antes de guardarse en la configuración. */
export function useOfferingEditor() {
  const { config, actions } = useConfig();
  const { saveOffering } = actions;
  const [editor, setEditor] = useState<EditorState | null>(null);
  const isCatalog = config.business.salesMode === "catalog";

  const startNew = useCallback(() => {
    const billing = isCatalog ? "one_time" : "monthly";
    setEditor({ draft: createOffering({ billing }), isNew: true, issues: [] });
  }, [isCatalog]);

  const startEdit = useCallback((offering: Offering) => {
    setEditor({ draft: { ...offering, features: [...offering.features], notIncluded: [...offering.notIncluded] }, isNew: false, issues: [] });
  }, []);

  const change = useCallback((patch: Partial<Offering>) => {
    setEditor((current) => (current ? { ...current, draft: { ...current.draft, ...patch } } : current));
  }, []);

  const cancel = useCallback(() => setEditor(null), []);

  /** Devuelve true si se guardó; si hay errores, los deja visibles en el formulario. */
  const save = useCallback((): boolean => {
    if (!editor) return false;
    const errors = validateOffering(editor.draft, isCatalog).filter((issue) => issue.severity === "error");
    if (errors.length > 0) {
      setEditor({ ...editor, issues: errors });
      return false;
    }
    saveOffering(editor.draft);
    setEditor(null);
    return true;
  }, [saveOffering, editor, isCatalog]);

  return { editor, startNew, startEdit, change, cancel, save };
}
