import { useCallback, useEffect, useState } from "react";
import type { AuthorizationDecision, AuthorizationPrompt } from "../repositories/agentAuthorization";
import { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";
import { useAgentAuthorizationService } from "./integrationsContext";

export type AgentAuthorizationState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; prompt: AuthorizationPrompt };

export interface AgentAuthorizationData {
  state: AgentAuthorizationState;
  /** Autoriza o rechaza. Devuelve a dónde ir (el agente) o los problemas por campo. */
  decide: (decision: Omit<AuthorizationDecision, "params">) => Promise<{ redirectTo: string } | { error: string; problems: Record<string, string> }>;
}

/** La pantalla de autorización: qué agente pide acceso (con los parámetros de la dirección) y la decisión de la persona. */
export function useAgentAuthorization(params: Record<string, string>): AgentAuthorizationData {
  const service = useAgentAuthorizationService();
  const [state, setState] = useState<AgentAuthorizationState>({ status: "loading" });
  const key = JSON.stringify(params);

  useEffect(() => {
    let active = true;
    service.describe(JSON.parse(key) as Record<string, string>).then(
      (prompt) => active && setState({ status: "ready", prompt }),
      (reason: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(reason) }),
    );
    return () => {
      active = false;
    };
  }, [service, key]);

  const decide = useCallback<AgentAuthorizationData["decide"]>(
    async (decision) => {
      try {
        return { redirectTo: await service.decide({ ...decision, params: JSON.parse(key) as Record<string, string> }) };
      } catch (reason) {
        const problems = reason instanceof PersistenceError ? Object.fromEntries(reason.problems.map((problem) => [problem.path, problem.message])) : {};
        return { error: persistenceErrorMessage(reason), problems };
      }
    },
    [service, key],
  );

  return { state, decide };
}
