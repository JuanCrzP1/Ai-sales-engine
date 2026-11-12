import { createAuthClient } from "@neon/auth";
import { createApiAssistantLab } from "../infrastructure/api/apiAssistantLab";
import { createApiAttention } from "../infrastructure/api/apiAttention";
import { createApiBusinessDirectory } from "../infrastructure/api/apiBusinessDirectory";
import { createApiChannels } from "../infrastructure/api/apiChannels";
import { createApiCommerce } from "../infrastructure/api/apiCommerce";
import { createApiConfigRepository } from "../infrastructure/api/apiConfigRepository";
import { createApiInbox } from "../infrastructure/api/apiInbox";
import { createHttpClient } from "../infrastructure/api/httpClient";
import { createBrowserPush } from "../infrastructure/browser/browserPush";
import { createLocalOperatorAuthService } from "../infrastructure/local/localOperatorAuthService";
import { createNeonAuthService, type NeonAuthClient } from "../infrastructure/neon/neonAuthService";
import type { AssistantLab } from "../repositories/assistantLab";
import type { Attention, DevicePush } from "../repositories/attention";
import type { AuthService } from "../repositories/authService";
import type { BusinessDirectory } from "../repositories/businessDirectory";
import type { Channels } from "../repositories/channels";
import type { Commerce } from "../repositories/commerce";
import type { ConfigRepository } from "../repositories/configRepository";
import type { Inbox } from "../repositories/inbox";

/**
 * Servicios de la aplicación. Es el ÚNICO punto donde se eligen las implementaciones: pantallas, estado y reglas solo
 * conocen los contratos de `repositories/`.
 */
export interface ApplicationServices {
  auth: AuthService;
  directory: BusinessDirectory;
  createConfigRepository: (slug: string) => ConfigRepository;
  /** Inteligencia artificial y área de pruebas de un negocio. */
  createAssistantLab: (slug: string) => AssistantLab;
  /** La bandeja de conversaciones de todos los negocios del usuario. */
  inbox: Inbox;
  /** Los canales de un negocio (por ahora, WhatsApp por código QR). */
  createChannels: (slug: string) => Channels;
  createCommerce: (slug: string) => Commerce;
  /** La atención humana de un negocio (Ajustes → Atención humana). */
  createAttention: (slug: string) => Attention;
  /** Las notificaciones en este navegador o celular (de la persona, no de un negocio). */
  devicePush: DevicePush;
}

/** Implementaciones actuales: la API local del panel, sin autenticación porque solo atiende en este equipo. */
export function createLocalServices(apiBaseUrl?: string): ApplicationServices {
  const http = createHttpClient(apiBaseUrl);
  return {
    auth: createLocalOperatorAuthService(),
    directory: createApiBusinessDirectory(http),
    createConfigRepository: (slug) => createApiConfigRepository(http, slug),
    createAssistantLab: (slug) => createApiAssistantLab(http, slug),
    inbox: createApiInbox(http),
    createChannels: (slug) => createApiChannels(http, slug),
    createCommerce: (slug) => createApiCommerce(http, slug),
    createAttention: (slug) => createApiAttention(http, slug),
    devicePush: createBrowserPush(http),
  };
}

/** En la nube: cuentas de Neon Auth y la API del panel con el token de la sesión en cada petición. */
export function createCloudServices(authUrl: string, apiBaseUrl?: string): ApplicationServices {
  const auth = createNeonAuthService(createAuthClient(authUrl) as unknown as NeonAuthClient);
  const http = createHttpClient(apiBaseUrl, { token: auth.token });
  return {
    auth,
    directory: createApiBusinessDirectory(http, { local: false }),
    createConfigRepository: (slug) => createApiConfigRepository(http, slug),
    createAssistantLab: (slug) => createApiAssistantLab(http, slug),
    inbox: createApiInbox(http),
    createChannels: (slug) => createApiChannels(http, slug),
    createCommerce: (slug) => createApiCommerce(http, slug),
    createAttention: (slug) => createApiAttention(http, slug),
    devicePush: createBrowserPush(http),
  };
}

/** La nube cuando el despliegue define `VITE_NEON_AUTH_URL` (Vercel); si no, este equipo. */
export function createServices(env: Record<string, unknown> = import.meta.env): ApplicationServices {
  const authUrl = typeof env.VITE_NEON_AUTH_URL === "string" ? env.VITE_NEON_AUTH_URL.trim() : "";
  return authUrl ? createCloudServices(authUrl) : createLocalServices();
}
