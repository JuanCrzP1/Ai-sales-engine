import { useEffect, useState } from "react";
import type { ModelCatalog } from "../repositories/assistantLab";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import { useAssistantLab } from "./assistantLabContext";

export type { AIModelOption, ModelCatalog } from "../repositories/assistantLab";

export type AIModelsState = { status: "loading" } | { status: "ready"; catalog: ModelCatalog } | { status: "error"; message: string };

/** La lista de modelos de OpenRouter para elegir el del asistente. */
export function useAIModels(): AIModelsState {
  const lab = useAssistantLab();
  const [state, setState] = useState<AIModelsState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    setState({ status: "loading" });
    lab.getAIModels().then(
      (catalog) => active && setState({ status: "ready", catalog }),
      (reason: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(reason) }),
    );
    return () => {
      active = false;
    };
  }, [lab]);

  return state;
}
