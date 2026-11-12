import { useCallback, useEffect, useState } from "react";
import type { AttentionSettings, AttentionView } from "../repositories/attention";
import { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";
import { useAttention } from "./attentionContext";

export interface TestEmailResult {
  ok: boolean;
  message: string;
}

export interface AttentionSettingsState {
  status: "loading" | "ready" | "error";
  view: AttentionView | null;
  error: string | null;
  /** Problemas por campo devueltos por el servidor (`team_hours[0].closes`, `email_to`...). */
  problems: Record<string, string>;
  saving: boolean;
  /** Verdadero justo después de guardar con éxito. */
  saved: boolean;
  sendingEmail: boolean;
  emailResult: TestEmailResult | null;
  save: (settings: AttentionSettings) => Promise<boolean>;
  sendTestEmail: () => Promise<void>;
  reload: () => void;
}

/** La atención humana del negocio abierto: cargar, guardar (se aplica al instante) y enviar un correo de prueba. */
export function useAttentionSettings(): AttentionSettingsState {
  const attention = useAttention();
  const [status, setStatus] = useState<AttentionSettingsState["status"]>("loading");
  const [view, setView] = useState<AttentionView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [problems, setProblems] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailResult, setEmailResult] = useState<TestEmailResult | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    setStatus("loading");
    attention.get().then(
      (loaded) => {
        if (!active) return;
        setView(loaded);
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
  }, [attention, attempt]);

  const save = useCallback<AttentionSettingsState["save"]>(
    async (settings) => {
      setSaving(true);
      setSaved(false);
      setError(null);
      setProblems({});
      try {
        setView(await attention.save(settings));
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
    [attention],
  );

  const sendTestEmail = useCallback(async () => {
    setSendingEmail(true);
    setEmailResult(null);
    try {
      const recipients = await attention.sendTestEmail();
      setEmailResult({ ok: true, message: `Te enviamos un correo de prueba a ${recipients.join(", ")}. Revisa también la carpeta de spam.` });
    } catch (reason) {
      setEmailResult({ ok: false, message: persistenceErrorMessage(reason) });
    } finally {
      setSendingEmail(false);
    }
  }, [attention]);

  const reload = useCallback(() => setAttempt((count) => count + 1), []);

  return { status, view, error, problems, saving, saved, sendingEmail, emailResult, save, sendTestEmail, reload };
}
