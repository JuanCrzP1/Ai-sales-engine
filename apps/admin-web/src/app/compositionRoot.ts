import { createLocalConfigRepository } from "../infrastructure/local/localConfigRepository";
import { createOpenAuthService } from "../infrastructure/local/openAuthService";
import type { AuthService } from "../repositories/authService";
import type { ConfigRepository } from "../repositories/configRepository";

/**
 * Servicios de la aplicación. Es el ÚNICO punto donde se eligen las implementaciones:
 * para conectar un servidor se crean implementaciones remotas de los contratos de
 * `repositories/` y se devuelven aquí, sin tocar pantallas, estado ni reglas.
 */
export interface ApplicationServices {
  auth: AuthService;
  createConfigRepository: (accountId: string) => ConfigRepository;
}

/** Implementaciones actuales: todo en este navegador, sin servidor y sin verificación de acceso. */
export function createLocalServices(): ApplicationServices {
  return {
    auth: createOpenAuthService(),
    createConfigRepository: (accountId) => createLocalConfigRepository(accountId),
  };
}
