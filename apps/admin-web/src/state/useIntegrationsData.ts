import { useCallback, useEffect, useState } from "react";
import type { ApiKey, CreatedApiKey, IntegrationsOverview } from "../repositories/integrations";
import { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";
import { useIntegrations } from "./integrationsContext";

export interface IntegrationsData {
  status: "loading" | "ready" | "error";
  overview: IntegrationsOverview | null;
  keys: ApiKey[];
  error: string | null;
  reload: () => void;
  /** Crea una clave; devuelve la clave con su valor completo (solo esta vez) o los problemas por campo. */
  createKey: (name: string, scopes: string[]) => Promise<{ created: CreatedApiKey } | { error: string; problems: Record<string, string> }>;
  revokeKey: (id: string) => Promise<string | null>;
}

/** Las integraciones del negocio abierto: su resumen y sus claves de API, con crear y revocar. */
export function useIntegrationsData(): IntegrationsData {
  const integrations = useIntegrations();
  const [status, setStatus] = useState<IntegrationsData["status"]>("loading");
  const [overview, setOverview] = useState<IntegrationsOverview | null>(null);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    Promise.all([integrations.overview(), integrations.keys()]).then(
      ([loadedOverview, loadedKeys]) => {
        if (!active) return;
        setOverview(loadedOverview);
        setKeys(loadedKeys);
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
  }, [integrations, attempt]);

  const reload = useCallback(() => setAttempt((count) => count + 1), []);

  const createKey = useCallback<IntegrationsData["createKey"]>(
    async (name, scopes) => {
      try {
        const created = await integrations.createKey(name, scopes);
        reload();
        return { created };
      } catch (reason) {
        const problems = reason instanceof PersistenceError ? Object.fromEntries(reason.problems.map((problem) => [problem.path, problem.message])) : {};
        return { error: persistenceErrorMessage(reason), problems };
      }
    },
    [integrations, reload],
  );

  const revokeKey = useCallback(
    async (id: string) => {
      try {
        await integrations.revokeKey(id);
        reload();
        return null;
      } catch (reason) {
        return persistenceErrorMessage(reason);
      }
    },
    [integrations, reload],
  );

  return { status, overview, keys, error, reload, createKey, revokeKey };
}
