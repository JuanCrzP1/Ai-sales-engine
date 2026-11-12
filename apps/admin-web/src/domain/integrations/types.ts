/**
 * Integraciones: conectar el asistente con otras herramientas.
 * - Claves de API: dejan que otro sistema use el negocio sin una sesión del panel. Se muestran una sola vez.
 * - API del asistente: otra plataforma (de automatización, una web, un servidor propio) manda el mensaje de un cliente y recibe la
 *   respuesta. Las guías por plataforma solo dicen «Probado» cuando se probó con un flujo real.
 */
import curlSample from "./samples/curl.txt?raw";
import javascriptSample from "./samples/javascript.txt?raw";
import pythonSample from "./samples/python.txt?raw";

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

/** El encabezado que lleva cada petición; «TU_CLAVE» se cambia por la clave creada. */
export const AUTHORIZATION_HEADER = "Authorization: Bearer TU_CLAVE";

/** Las cabeceras de cada petición, como nombre y valor (así las piden las plataformas). */
export const REQUEST_HEADERS: { name: string; value: string; hint?: string }[] = [
  { name: "Authorization", value: "Bearer TU_CLAVE", hint: "Cambia TU_CLAVE por tu clave (empieza por ase_live_). Deja «Bearer» y un espacio antes." },
  { name: "Content-Type", value: "application/json" },
];

/** Un cuerpo de ejemplo con datos de verdad: lo que cualquier plataforma debe mandar. */
export const EXAMPLE_REQUEST_BODY = '{"contact": {"id": "573001112233", "name": "Laura"}, "message": "Hola, ¿qué precios tienen?"}';

/**
 * Leona (probado el 12 de noviembre de 2026 con un flujo real). Sus variables del sistema son `{phone_number}` y `{full_name}`;
 * sus campos personalizados se escriben sin prefijo (`{ase_mensaje}`). Ojo: su botón «Probar petición» no cambia las variables.
 */
export const LEONA = {
  messageField: "ase_mensaje",
  replyField: "ase_respuesta",
  handoffField: "ase_handoff",
  requestBody: '{"contact": {"id": "{phone_number}", "name": "{full_name}"}, "message": "{ase_mensaje}"}',
} as const;

export type CodeLanguage = "curl" | "javascript" | "python";

const CODE_SAMPLES: Record<CodeLanguage, string> = { curl: curlSample, javascript: javascriptSample, python: pythonSample };

export const CODE_LANGUAGES: { value: CodeLanguage; label: string }[] = [
  { value: "curl", label: "cURL" },
  { value: "javascript", label: "JavaScript" },
  { value: "python", label: "Python" },
];

/**
 * El mismo pedido en cada lenguaje, para quien programa su propia integración. Los ejemplos son texto para copiar (`samples/*.txt`),
 * no código del panel: así las pruebas que vigilan las llamadas y las variables de entorno del panel no los confunden con las suyas.
 */
export function codeExample(language: CodeLanguage, url: string): string {
  return CODE_SAMPLES[language].trimEnd().replaceAll("{{URL}}", url);
}

/** Si alguna plataforma ya está usando la API: el último uso de las claves activas para conversar. */
export type ConnectionState = { kind: "connected"; lastUsedAt: string } | { kind: "ready" } | { kind: "no-key" };

export function connectionState(keys: ApiKey[]): ConnectionState {
  const chatKeys = keys.filter((key) => key.active && key.scopes.includes(SCOPE_ASSISTANT_CHAT));
  if (chatKeys.length === 0) return { kind: "no-key" };
  const lastUsed = chatKeys.map((key) => key.lastUsedAt).filter((value): value is string => value !== null).sort().pop();
  return lastUsed ? { kind: "connected", lastUsedAt: lastUsed } : { kind: "ready" };
}
