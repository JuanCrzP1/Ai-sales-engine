import { useEffect, useState } from "react";
import type { AIUsage } from "../repositories/assistantLab";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import { useAssistantLab } from "./assistantLabContext";

export type { AIUsage } from "../repositories/assistantLab";

export type AIUsageState = { status: "loading" } | { status: "ready"; usage: AIUsage } | { status: "error"; message: string };

/** El consumo de IA del negocio abierto en los últimos 30 días. */
export function useAIUsage(): AIUsageState {
  const lab = useAssistantLab();
  const [state, setState] = useState<AIUsageState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    setState({ status: "loading" });
    lab.getAIUsage().then(
      (usage) => active && setState({ status: "ready", usage }),
      (reason: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(reason) }),
    );
    return () => {
      active = false;
    };
  }, [lab]);

  return state;
}
