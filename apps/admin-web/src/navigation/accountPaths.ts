/** Rutas de cuenta: fuera del recorrido de configuración. Se usarán cuando exista la autenticación definitiva. */
export const ACCOUNT_PATHS = {
  signIn: "/iniciar-sesion",
  signUp: "/crear-cuenta",
  profile: "/perfil",
  /** Donde un agente (Claude, ChatGPT) pide conectarse con inicio de sesión. La anuncia el motor (`AUTHORIZE_PAGE_PATH`). */
  agentAuthorization: "/oauth/authorize",
} as const;

/** Destino tras iniciar sesión: la página que se intentó abrir, si existe. */
export function redirectTarget(state: unknown): string {
  const from = (state as { from?: unknown } | null)?.from;
  const isAuthPage = from === ACCOUNT_PATHS.signIn || from === ACCOUNT_PATHS.signUp;
  return typeof from === "string" && from.startsWith("/") && !from.startsWith("//") && !isAuthPage ? from : "/";
}
