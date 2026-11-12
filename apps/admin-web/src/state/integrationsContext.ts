import { createContext, useContext } from "react";
import type { AgentAuthorization } from "../repositories/agentAuthorization";
import type { Integrations } from "../repositories/integrations";

/** Las integraciones del negocio abierto. Las entrega el espacio de trabajo del negocio. */
export const IntegrationsContext = createContext<Integrations | null>(null);

export function useIntegrations(): Integrations {
  const integrations = useContext(IntegrationsContext);
  if (!integrations) throw new Error("useIntegrations debe usarse dentro del espacio de trabajo de un negocio.");
  return integrations;
}

/** Autorizar a un agente que se conecta iniciando sesión. Lo entrega la aplicación: es de la cuenta, no de un negocio. */
export const AgentAuthorizationContext = createContext<AgentAuthorization | null>(null);

export function useAgentAuthorizationService(): AgentAuthorization {
  const service = useContext(AgentAuthorizationContext);
  if (!service) throw new Error("useAgentAuthorizationService debe usarse dentro de <App>.");
  return service;
}
