import { createApiBusinessDirectory } from "../infrastructure/api/apiBusinessDirectory";
import { createApiConfigRepository } from "../infrastructure/api/apiConfigRepository";
import { createHttpClient } from "../infrastructure/api/httpClient";
import { createLocalOperatorAuthService } from "../infrastructure/local/localOperatorAuthService";
import type { AuthService } from "../repositories/authService";
import type { BusinessDirectory } from "../repositories/businessDirectory";
import type { ConfigRepository } from "../repositories/configRepository";

/**
 * Servicios de la aplicación. Es el ÚNICO punto donde se eligen las implementaciones: pantallas, estado y reglas solo
 * conocen los contratos de `repositories/`. La autenticación definitiva (fase de nube) se conecta aquí.
 */
export interface ApplicationServices {
  auth: AuthService;
  directory: BusinessDirectory;
  createConfigRepository: (slug: string) => ConfigRepository;
}

/** Implementaciones actuales: la API local del panel, sin autenticación porque solo atiende en este equipo. */
export function createLocalServices(apiBaseUrl?: string): ApplicationServices {
  const http = createHttpClient(apiBaseUrl);
  return {
    auth: createLocalOperatorAuthService(),
    directory: createApiBusinessDirectory(http),
    createConfigRepository: (slug) => createApiConfigRepository(http, slug),
  };
}
