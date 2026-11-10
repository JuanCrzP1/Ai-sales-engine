import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

/** La API local del panel. Solo escucha en este equipo: ver `scripts/run_admin_api.py`. */
const { ADMIN_API_PORT = "8010" } = loadEnv("", ".", "ADMIN_API_");
/** La interfaz. No usa el 5173 que Vite toma por defecto, para convivir con otros proyectos de Vite en este equipo. La API, los
 *  lanzadores y el script `panel` lo repiten porque no pueden leerlo de aquí: `tests/test_admin_api.py` comprueba que coincidan. */
const ADMIN_WEB_PORT = 5180;
const LOCAL_SERVER = { host: "127.0.0.1", port: ADMIN_WEB_PORT, strictPort: true, proxy: { "/api": `http://127.0.0.1:${ADMIN_API_PORT}` } };

export default defineConfig({
  plugins: [react()],
  server: LOCAL_SERVER,
  preview: { ...LOCAL_SERVER, port: 4173 },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    // Escribir tecla a tecla sobre la aplicación completa en jsdom es lento; un plazo corto dejaría teclas sueltas en la prueba siguiente.
    testTimeout: 30_000,
    // Las pruebas de integración necesitan la API real: se ejecutan con `npm run test:integration`.
    include: ["src/**/*.test.{ts,tsx}"],
    exclude: ["src/test/integration/**"],
    // La prueba de arquitectura lista el código con import.meta.glob; con la caché persistente de
    // módulos transformados no vería archivos nuevos y podría aprobar violaciones reales.
    fsModuleCache: false,
  },
});
