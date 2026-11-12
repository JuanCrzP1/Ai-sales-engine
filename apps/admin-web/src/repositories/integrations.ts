import type { ApiKey, AssistantApiReply, CreatedApiKey, IntegrationsOverview } from "../domain/integrations/types";

export type { ApiKey, AssistantApiReply, CreatedApiKey, IntegrationsOverview } from "../domain/integrations/types";

/** Las integraciones de un negocio. Los fallos se rechazan con `PersistenceError`, con un mensaje y los problemas por campo. */
export interface Integrations {
  overview(): Promise<IntegrationsOverview>;
  keys(): Promise<ApiKey[]>;
  /** Crea una clave: su valor completo solo viene en esta respuesta. */
  createKey(name: string, scopes: string[]): Promise<CreatedApiKey>;
  revokeKey(id: string): Promise<ApiKey>;
  /** Lo que respondería la API del asistente a ese mensaje, con lo publicado (gasta la clave de IA, como «Probar»). */
  tryAssistantApi(message: string): Promise<AssistantApiReply>;
}
