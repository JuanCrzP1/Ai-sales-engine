import { useCallback } from "react";
import type { CatalogItem, Plan } from "../../domain/config/types";
import { categoryName, isCatalog, type OfferEntry } from "../../domain/config/document";
import { createCatalogItem, createPlan } from "../../domain/config/factories";
import { validateEntry } from "../../domain/validation/rules";
import { useConfig } from "../../state/useConfig";

/**
 * Borrador de un plan o producto: se valida antes de pasar a la lista y se guarda con el resto de la configuración. Lo
 * conserva el estado de la configuración, así que lo escrito sigue ahí al volver de otra sección.
 */
export function useOfferingEditor() {
  const { document, actions, offeringDraft: editor } = useConfig();
  const { savePlan, saveCatalogItem, setOfferingDraft } = actions;
  const catalog = isCatalog(document);

  const startNew = useCallback(() => {
    const draft = catalog ? createCatalogItem() : createPlan({ payment_profile: document.payments[0]?.id ?? null });
    setOfferingDraft({ draft, categoryName: "", isNew: true, issues: [], touched: false });
  }, [catalog, document.payments, setOfferingDraft]);

  const startEdit = useCallback(
    (entry: OfferEntry) => {
      setOfferingDraft({ draft: structuredClone(entry), categoryName: catalog ? categoryName(document, (entry as CatalogItem).category) : "", isNew: false, issues: [], touched: false });
    },
    [catalog, document, setOfferingDraft],
  );

  const change = useCallback(
    (patch: Partial<Plan & CatalogItem>) => {
      setOfferingDraft((current) => (current ? { ...current, draft: { ...current.draft, ...patch } as OfferEntry, touched: true } : current));
    },
    [setOfferingDraft],
  );

  const changeCategory = useCallback(
    (name: string) => {
      setOfferingDraft((current) => (current ? { ...current, categoryName: name, touched: true } : current));
    },
    [setOfferingDraft],
  );

  const cancel = useCallback(() => setOfferingDraft(null), [setOfferingDraft]);

  /** Devuelve true si pasó a la lista; si hay errores, los deja visibles en el formulario. */
  const save = useCallback((): boolean => {
    if (!editor) return false;
    const errors = validateEntry(editor.draft, catalog, catalog ? editor.categoryName : undefined).filter((issue) => issue.severity === "error");
    if (errors.length > 0) {
      setOfferingDraft({ ...editor, issues: errors });
      return false;
    }
    if (catalog) saveCatalogItem(editor.draft as CatalogItem, editor.categoryName);
    else savePlan(editor.draft as Plan);
    setOfferingDraft(null);
    return true;
  }, [saveCatalogItem, savePlan, setOfferingDraft, editor, catalog]);

  return { editor, startNew, startEdit, change, changeCategory, cancel, save };
}
