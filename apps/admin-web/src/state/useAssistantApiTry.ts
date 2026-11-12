import { useCallback, useState } from "react";
import type { AssistantApiReply } from "../repositories/integrations";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import { useIntegrations } from "./integrationsContext";

/** Probar la API del asistente desde el panel: lo que respondería a un mensaje, con lo publicado. */
export function useAssistantApiTry() {
  const integrations = useIntegrations();
  const [trying, setTrying] = useState(false);
  const [result, setResult] = useState<AssistantApiReply | null>(null);
  const [error, setError] = useState<string | null>(null);

  const send = useCallback(
    async (message: string) => {
      setTrying(true);
      setError(null);
      setResult(null);
      try {
        setResult(await integrations.tryAssistantApi(message));
      } catch (reason) {
        setError(persistenceErrorMessage(reason));
      } finally {
        setTrying(false);
      }
    },
    [integrations],
  );

  return { trying, result, error, send };
}
