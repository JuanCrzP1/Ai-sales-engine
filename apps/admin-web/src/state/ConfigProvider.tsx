import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { createEmptyConfig } from "../domain/config/factories";
import * as operations from "../domain/config/operations";
import type { AssistantConfig } from "../domain/config/types";
import { computeProgress } from "../domain/validation/progress";
import { validateConfig } from "../domain/validation/rules";
import type { ConfigRepository } from "../repositories/configRepository";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import { ConfigContext, type ConfigActions, type ConfigContextValue, type SaveState } from "./configContext";

type LoadState = { status: "loading" } | { status: "error"; message: string } | { status: "ready" };

export interface ConfigLoadErrorProps {
  message: string;
  retry: () => void;
  /** Descarta lo guardado (ilegible) y empieza con una configuración vacía. Acción explícita. */
  discard: () => void;
}

interface ConfigProviderProps {
  repository: ConfigRepository;
  children: ReactNode;
  renderLoading: () => ReactNode;
  renderError: (props: ConfigLoadErrorProps) => ReactNode;
}

const INITIAL_SAVE: SaveState = { status: "idle", savedAt: null, error: null };

/**
 * Carga la configuración de la cuenta, la valida y guarda cada cambio en su repositorio.
 * Los guardados se encadenan en orden y el estado solo pasa a "saved" cuando se confirman.
 */
export function ConfigProvider({ repository, children, renderLoading, renderError }: ConfigProviderProps) {
  const [load, setLoad] = useState<LoadState>({ status: "loading" });
  const [config, setConfig] = useState<AssistantConfig>(createEmptyConfig);
  const [save, setSave] = useState<SaveState>(INITIAL_SAVE);
  const [attempt, setAttempt] = useState(0);
  /** Última configuración confirmada por el almacenamiento (o la cargada). */
  const persisted = useRef<AssistantConfig | null>(null);
  const queue = useRef<Promise<unknown>>(Promise.resolve());
  const sequence = useRef(0);
  /** Configuración vigente, para reintentar el guardado sin depender del render. */
  const latest = useRef(config);

  useEffect(() => {
    latest.current = config;
  }, [config]);

  useEffect(() => {
    let active = true;
    setLoad({ status: "loading" });
    repository.load().then(
      (stored) => {
        if (!active) return;
        const loaded = stored?.config ?? createEmptyConfig();
        persisted.current = loaded;
        setConfig(loaded);
        setSave({ ...INITIAL_SAVE, savedAt: stored?.savedAt ?? null });
        setLoad({ status: "ready" });
      },
      (error: unknown) => {
        if (active) setLoad({ status: "error", message: persistenceErrorMessage(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [repository, attempt]);

  const persist = useCallback(
    (snapshot: AssistantConfig) => {
      const current = ++sequence.current;
      setSave((previous) => ({ ...previous, status: "saving", error: null }));
      const operation = queue.current.then(() => repository.save(snapshot));
      queue.current = operation.catch(() => undefined);
      operation.then(
        (stored) => {
          persisted.current = snapshot;
          if (current === sequence.current) setSave({ status: "saved", savedAt: stored.savedAt, error: null });
        },
        (error: unknown) => {
          if (current === sequence.current) {
            setSave((previous) => ({ ...previous, status: "error", error: persistenceErrorMessage(error) }));
          }
        },
      );
    },
    [repository],
  );

  useEffect(() => {
    if (load.status !== "ready" || config === persisted.current) return;
    persist(config);
  }, [config, load.status, persist]);

  const actions = useMemo<ConfigActions>(() => {
    const apply = (change: (current: AssistantConfig) => AssistantConfig) => setConfig(change);
    return {
      updateSection: (section, patch) => apply((current) => operations.updateSection(current, section, patch)),
      saveOffering: (offering) => apply((current) => operations.saveOffering(current, offering)),
      removeOffering: (id) => apply((current) => operations.removeOffering(current, id)),
      setOfferingAvailability: (id, available) => apply((current) => operations.setOfferingAvailability(current, id, available)),
      addTransferMethod: () => apply((current) => operations.addTransferMethod(current)),
      updateTransferMethod: (id, details) => apply((current) => operations.updateTransferMethod(current, id, details)),
      changeTransferMethodType: (id, type) => apply((current) => operations.changeTransferMethodType(current, id, type)),
      removeTransferMethod: (id) => apply((current) => operations.removeTransferMethod(current, id)),
      resetConfig: () => apply(() => createEmptyConfig()),
      retrySave: () => persist(latest.current),
    };
  }, [persist]);

  const issues = useMemo(() => validateConfig(config), [config]);
  const progress = useMemo(() => computeProgress(issues), [issues]);
  const value = useMemo<ConfigContextValue>(() => ({ config, issues, progress, save, actions }), [config, issues, progress, save, actions]);

  if (load.status === "loading") return <>{renderLoading()}</>;
  if (load.status === "error") {
    return (
      <>
        {renderError({
          message: load.message,
          retry: () => setAttempt((count) => count + 1),
          discard: () => {
            repository.clear().then(
              () => setAttempt((count) => count + 1),
              (error: unknown) => setLoad({ status: "error", message: persistenceErrorMessage(error) }),
            );
          },
        })}
      </>
    );
  }
  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>;
}
