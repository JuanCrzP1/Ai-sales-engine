/**
 * Integraciones: conectar el asistente con otras herramientas.
 * - Claves de API: dejan que otro sistema use el negocio sin una sesión del panel. Se muestran una sola vez.
 * - API del asistente: otro sistema (Leona, una web) manda el mensaje de un cliente y recibe la respuesta.
 */

/** Conversar con el asistente (la API del asistente). Los permisos para configurar llegarán con el servidor MCP. */
export const SCOPE_ASSISTANT_CHAT = "assistant:chat";

export interface ApiKey {
  id: string;
  name: string;
  /** El comienzo visible (`ase_live_Ab12Cd`), para reconocerla. */
  prefix: string;
  scopes: string[];
  createdAt: string;
  createdBy: string | null;
  lastUsedAt: string | null;
  revokedAt: string | null;
  active: boolean;
}

/** Una clave recién creada: la única vez que se ve completa. */
export interface CreatedApiKey {
  key: ApiKey;
  secret: string;
}

export interface IntegrationsOverview {
  /** La dirección pública de la API del asistente, o null si el motor no tiene una (en este equipo sin ngrok). */
  assistantApiUrl: string | null;
  chatKeys: number;
  activeKeys: number;
  scopes: { id: string; label: string }[];
}

/** Lo que responde la API del asistente (ver docs/api.md). */
export interface AssistantApiReply {
  conversation_id: string;
  reply: string;
  parts: string[];
  handoff: boolean;
  handoff_reason: string | null;
  attended_by: "assistant" | "team";
  intent: string | null;
  stage: string;
  fallback: boolean;
  duplicate: boolean;
}

/** El cuerpo que arma Leona en su bloque «Integración HTTP», con sus variables. */
export const LEONA_REQUEST_BODY = '{"contact": {"id": "{customer.phone}", "name": "{customer.name}"}, "message": "{last_message}"}';

/** Un ejemplo para probar desde la terminal. */
export function curlExample(url: string): string {
  return [
    `curl -X POST "${url}" \\`,
    '  -H "Authorization: Bearer TU_CLAVE" \\',
    '  -H "Content-Type: application/json" \\',
    `  -d '{"contact": {"id": "573001112233", "name": "Laura"}, "message": "Hola, ¿qué precios tienen?"}'`,
  ].join("\n");
}
