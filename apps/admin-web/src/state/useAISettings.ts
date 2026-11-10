import { useCallback, useEffect, useState } from "react";
import type { AISettings, KeyCheck } from "../repositories/assistantLab";
import { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";
import { useAssistantLab } from "./assistantLabContext";

export type { AISettings, KeyCheck } from "../repositories/assistantLab";

export interface AISettingsState {
  status: "loading" | "ready" | "error";
  settings: AISettings | null;
  /** Mensaje para mostrar si falló la carga o el guardado. */
  error: string | null;
  /** Problemas por campo devueltos por el servidor (`model`, `api_key`). */
  problems: Record<string, string>;
  saving: boolean;
  checking: boolean;
  check: KeyCheck | null;
  /** Verdadero justo después de guardar con éxito. */
  saved: boolean;
  save: (input: { model: string; apiKey: string; clearKey?: boolean }) => Promise<boolean>;
  verify: () => Promise<void>;
  reload: () => void;
}

/** La inteligencia artificial del negocio abierto: cargar, guardar y comprobar su clave. La clave escrita nunca se conserva aquí. */
export function useAISettings(): AISettingsState {
  const lab = useAssistantLab();
  const [status, setStatus] = useState<AISettingsState["status"]>("loading");
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [problems, setProblems] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [checking, setChecking] = useState(false);
  const [check, setCheck] = useState<KeyCheck | null>(null);
  const [saved, setSaved] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    setStatus("loading");
    lab.getAISettings().then(
      (loaded) => {
        if (!active) return;
        setSettings(loaded);
        setStatus("ready");
      },
      (reason: unknown) => {
        if (!active) return;
        setError(persistenceErrorMessage(reason));
        setStatus("error");
      },
    );
    return () => {
      active = false;
    };
  }, [lab, attempt]);

  const save = useCallback<AISettingsState["save"]>(
    async ({ model, apiKey, clearKey }) => {
      setSaving(true);
      setSaved(false);
      setError(null);
      setProblems({});
      setCheck(null);
      try {
        const updated = await lab.saveAISettings({ model: model.trim() || null, ...(apiKey.trim() ? { apiKey: apiKey.trim() } : {}), ...(clearKey ? { clearKey } : {}) });
        setSettings(updated);
        setSaved(true);
        return true;
      } catch (reason) {
        setError(persistenceErrorMessage(reason));
        if (reason instanceof PersistenceError) setProblems(Object.fromEntries(reason.problems.map((problem) => [problem.path, problem.message])));
        return false;
      } finally {
        setSaving(false);
      }
    },
    [lab],
  );

  const verify = useCallback(async () => {
    setChecking(true);
    setCheck(null);
    try {
      setCheck(await lab.verifyAIKey());
    } catch (reason) {
      setCheck({ valid: false, message: persistenceErrorMessage(reason) });
    } finally {
      setChecking(false);
    }
  }, [lab]);

  const reload = useCallback(() => setAttempt((count) => count + 1), []);

  return { status, settings, error, problems, saving, checking, check, saved, save, verify, reload };
}
