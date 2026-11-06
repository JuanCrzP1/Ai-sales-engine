import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { pathLabel } from "../domain/config/contractSchema";
import { paymentValuesToSend, sameDocument } from "../domain/config/document";
import { createEmptyDocument } from "../domain/config/factories";
import * as operations from "../domain/config/operations";
import type { BusinessDocument, PaymentFields, WorkingCopy } from "../domain/config/types";
import { sectionForPath } from "../domain/sections";
import { splitBySeverity } from "../domain/validation/issues";
import { computeProgress } from "../domain/validation/progress";
import { validateDocument, validatePaymentValues } from "../domain/validation/rules";
import type { ValidationIssue } from "../domain/validation/types";
import type { ConfigRepository, StoredConfig } from "../repositories/configRepository";
import { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";
import { ConfigContext, type ActionResult, type ConfigActions, type ConfigContextValue, type ConfigMeta, type OfferingDraft, type SaveState } from "./configContext";

type LoadState = { status: "loading" } | { status: "error"; message: string; notFound: boolean } | { status: "ready" };

export interface ConfigLoadErrorProps {
  message: string;
  notFound: boolean;
  retry: () => void;
}

interface ConfigProviderProps {
  slug: string;
  repository: ConfigRepository;
  children: ReactNode;
  renderLoading: () => ReactNode;
  renderError: (props: ConfigLoadErrorProps) => ReactNode;
}

const INITIAL_SAVE: SaveState = { status: "idle", savedAt: null, error: null, problems: [] };
const OPEN_DRAFT_MESSAGE = "Tienes un producto o plan abierto sin aplicar. Aplícalo a la lista o cancélalo antes de guardar.";

function problemsOf(error: unknown): ValidationIssue[] {
  if (!(error instanceof PersistenceError)) return [];
  return error.problems.map((problem) => {
    const label = pathLabel(problem.path);
    return { section: sectionForPath(problem.path), field: problem.path, severity: "error", message: problem.message, ...(label ? { label } : {}) };
  });
}

/**
 * Lo pendiente en cada campo. Si la validación anticipada ya señala un campo, se muestra su mensaje, escrito para el
 * negocio; el del servidor aparece en los demás campos y siempre en el resumen del intento de guardar.
 */
function mergeIssues(local: ValidationIssue[], problems: ValidationIssue[]): ValidationIssue[] {
  const { errors, warnings } = splitBySeverity(local);
  const flagged = new Set(errors.map((issue) => issue.field));
  return [...errors, ...problems.filter((problem) => !flagged.has(problem.field)), ...warnings];
}

/**
 * Carga el documento del negocio y mantiene lo que se está editando. Los cambios se guardan cuando el usuario lo pide,
 * porque cada guardado crea una versión. El servidor valida con el contrato: "Guardado" solo aparece si los aceptó.
 */
export function ConfigProvider({ slug, repository, children, renderLoading, renderError }: ConfigProviderProps) {
  const [load, setLoad] = useState<LoadState>({ status: "loading" });
  const [working, setWorking] = useState<WorkingCopy>(() => ({ document: createEmptyDocument(slug, ""), paymentValues: {} }));
  const [baseline, setBaseline] = useState<BusinessDocument>(working.document);
  const [paymentFields, setPaymentFields] = useState<PaymentFields>({});
  const [offeringDraft, setOfferingDraft] = useState<OfferingDraft | null>(null);
  const [meta, setMeta] = useState<ConfigMeta>({ slug, version: null, latestVersion: null, publishedVersion: null });
  const [save, setSave] = useState<SaveState>(INITIAL_SAVE);
  const [attempt, setAttempt] = useState(0);
  /** Valores vigentes para guardar sin depender del render. */
  const latest = useRef({ working, meta, offeringDraft });
  latest.current = { working, meta, offeringDraft };

  const applyStored = useCallback(
    (stored: StoredConfig) => {
      const document = stored.document ?? createEmptyDocument(slug, stored.name);
      setWorking({ document, paymentValues: {} });
      setBaseline(document);
      setPaymentFields(stored.paymentFields);
      setOfferingDraft(null);
      setMeta({ slug, version: stored.version, latestVersion: stored.latestVersion, publishedVersion: stored.publishedVersion });
    },
    [slug],
  );

  useEffect(() => {
    let active = true;
    setLoad({ status: "loading" });
    repository.load().then(
      (stored) => {
        if (!active) return;
        applyStored(stored);
        setSave({ ...INITIAL_SAVE, savedAt: stored.version?.createdAt ?? null });
        setLoad({ status: "ready" });
      },
      (error: unknown) => {
        if (active) setLoad({ status: "error", message: persistenceErrorMessage(error), notFound: error instanceof PersistenceError && error.code === "not_found" });
      },
    );
    return () => {
      active = false;
    };
  }, [repository, attempt, applyStored]);

  const actions = useMemo<ConfigActions>(() => {
    /** Un cambio deja atrás los errores del último intento de guardar. */
    const clearSaveError = () => setSave((previous) => (previous.status === "error" ? { ...previous, status: "idle", error: null, problems: [] } : previous));
    const edit = (change: (current: WorkingCopy) => WorkingCopy) => {
      setWorking(change);
      clearSaveError();
    };
    const editDocument = (change: (document: BusinessDocument) => BusinessDocument) => edit((current) => ({ ...current, document: change(current.document) }));

    const run = async (operation: () => Promise<StoredConfig>): Promise<ActionResult> => {
      try {
        const stored = await operation();
        applyStored(stored);
        setSave({ ...INITIAL_SAVE, savedAt: stored.version?.createdAt ?? null });
        return { ok: true };
      } catch (error) {
        return { ok: false, error: persistenceErrorMessage(error) };
      }
    };

    return {
      updateSection: (section, patch) => editDocument((document) => operations.updateSection(document, section, patch)),
      setRootValue: (key, value) => editDocument((document) => operations.setRootValue(document, key, value)),
      savePlan: (plan) => editDocument((document) => operations.savePlan(document, plan)),
      saveCatalogItem: (item, category) => editDocument((document) => operations.saveCatalogItem(document, item, category)),
      removeEntry: (id) => {
        editDocument((document) => operations.removeEntry(document, id));
        setOfferingDraft((current) => (current?.draft.id === id ? null : current));
      },
      setEntryAvailability: (id, available) => editDocument((document) => operations.setEntryAvailability(document, id, available)),
      switchOfferModel: (model) => {
        editDocument((document) => operations.switchOfferModel(document, model));
        // Un plan abierto no sirve en un catálogo, ni al revés: cambiar la forma de venta ya pide confirmación.
        setOfferingDraft(null);
      },
      renameCategory: (id, name) => editDocument((document) => operations.renameCategory(document, id, name)),
      removeCategory: (id) => editDocument((document) => operations.removeCategory(document, id)),
      setOfferingDraft: (update) => {
        setOfferingDraft(update);
        clearSaveError();
      },
      addPaymentProfile: () => edit(operations.addPaymentProfile),
      removePaymentProfile: (profileId) => edit((current) => operations.removePaymentProfile(current, profileId)),
      setPaymentLinkEnabled: (profileId, enabled) => edit((current) => operations.setPaymentLinkEnabled(current, profileId, enabled)),
      removePaymentLink: (profileId) => edit((current) => operations.removePaymentLink(current, profileId)),
      setPaymentValue: (ref, value) => edit((current) => operations.setPaymentValue(current, ref, value)),
      keepStoredPaymentValue: (ref) => edit((current) => operations.keepStoredPaymentValue(current, ref)),
      setTransferEnabled: (profileId, enabled) => edit((current) => operations.setTransferEnabled(current, profileId, enabled)),
      addTransferMethod: (profileId) => edit((current) => operations.addTransferMethod(current, profileId)),
      removeTransferMethod: (profileId, index) => edit((current) => operations.removeTransferMethod(current, profileId, index)),
      updateTransferMethod: (profileId, index, patch) => edit((current) => operations.updateTransferMethod(current, profileId, index, patch)),
      setTransferMethodEnabled: (profileId, index, enabled) => edit((current) => operations.setTransferMethodEnabled(current, profileId, index, enabled)),
      changeTransferMethodType: (profileId, index, type) => edit((current) => operations.changeTransferMethodType(current, profileId, index, type)),

      save: async () => {
        const { working: current, meta: currentMeta, offeringDraft: openDraft } = latest.current;
        if (openDraft?.touched) {
          const problem: ValidationIssue = { section: sectionForPath("offer"), field: "offer", severity: "error", message: OPEN_DRAFT_MESSAGE };
          setSave((previous) => ({ ...previous, status: "error", error: OPEN_DRAFT_MESSAGE, problems: [problem] }));
          return false;
        }
        if (validatePaymentValues(current).some((issue) => issue.severity === "error")) {
          setSave((previous) => ({ ...previous, status: "error", error: "Revisa los datos de pago marcados en Pagos y cierre.", problems: [] }));
          return false;
        }
        setSave((previous) => ({ ...previous, status: "saving", error: null, problems: [] }));
        try {
          const stored = await repository.save({ document: current.document, paymentValues: paymentValuesToSend(current), baseVersion: currentMeta.latestVersion });
          applyStored(stored);
          setSave({ ...INITIAL_SAVE, status: "saved", savedAt: stored.version?.createdAt ?? null });
          return true;
        } catch (error) {
          setSave((previous) => ({ ...previous, status: "error", error: persistenceErrorMessage(error), problems: problemsOf(error) }));
          return false;
        }
      },
      discardChanges: () => {
        setOfferingDraft(null);
        setAttempt((count) => count + 1);
      },
      loadReview: () => repository.review(),
      loadHistory: () => repository.history(),
      publish: (version) => run(() => repository.publish(version)),
      rollback: () => run(() => repository.rollback()),
      restore: (version) => run(() => repository.restore(version)),
    };
  }, [repository, applyStored]);

  const dirty = useMemo(
    () => !sameDocument(working.document, baseline) || Object.keys(paymentValuesToSend(working)).length > 0 || Boolean(offeringDraft?.touched),
    [working, baseline, offeringDraft],
  );
  const issues = useMemo(() => mergeIssues(validateDocument(working), save.problems), [working, save.problems]);
  const progress = useMemo(() => computeProgress(issues), [issues]);
  const value = useMemo<ConfigContextValue>(
    () => ({ document: working.document, paymentValues: working.paymentValues, paymentFields, offeringDraft, meta, dirty, issues, progress, save, actions }),
    [working, paymentFields, offeringDraft, meta, dirty, issues, progress, save, actions],
  );

  if (load.status === "loading") return <>{renderLoading()}</>;
  if (load.status === "error") return <>{renderError({ message: load.message, notFound: load.notFound, retry: () => setAttempt((count) => count + 1) })}</>;
  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>;
}
