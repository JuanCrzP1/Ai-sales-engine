/** Rutas de cuenta: fuera del recorrido de configuración. */
export const ACCOUNT_PATHS = {
  signIn: "/iniciar-sesion",
  signUp: "/crear-cuenta",
  profile: "/perfil",
} as const;

/** Destino tras iniciar sesión: la página que se intentó abrir, si existe. */
export function redirectTarget(state: unknown): string {
  const from = (state as { from?: unknown } | null)?.from;
  const isAuthPage = from === ACCOUNT_PATHS.signIn || from === ACCOUNT_PATHS.signUp;
  return typeof from === "string" && from.startsWith("/") && !from.startsWith("//") && !isAuthPage ? from : "/";
}
