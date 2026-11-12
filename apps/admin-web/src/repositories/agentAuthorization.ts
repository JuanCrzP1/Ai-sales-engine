import type { AuthorizationDecision, AuthorizationPrompt } from "../domain/integrations/types";

export type { AuthorizationDecision, AuthorizationPrompt } from "../domain/integrations/types";

/**
 * Conectar un agente con inicio de sesión (Claude web y app, ChatGPT): la persona, con su sesión, ve qué agente pide acceso y lo
 * autoriza con los permisos que elija, o lo rechaza. Es de la cuenta, no de un negocio. Los fallos se rechazan con `PersistenceError`.
 */
export interface AgentAuthorization {
  /** Qué agente pide acceso, con los parámetros que puso en la dirección. */
  describe(params: Record<string, string>): Promise<AuthorizationPrompt>;
  /** A dónde vuelve el navegador: al agente con el código (o con el rechazo). */
  decide(decision: AuthorizationDecision): Promise<string>;
}
