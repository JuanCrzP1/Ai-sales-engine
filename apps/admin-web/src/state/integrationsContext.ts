import { createContext, useContext } from "react";
import type { Integrations } from "../repositories/integrations";

/** Las integraciones del negocio abierto. Las entrega el espacio de trabajo del negocio. */
export const IntegrationsContext = createContext<Integrations | null>(null);

export function useIntegrations(): Integrations {
  const integrations = useContext(IntegrationsContext);
  if (!integrations) throw new Error("useIntegrations debe usarse dentro del espacio de trabajo de un negocio.");
  return integrations;
}
