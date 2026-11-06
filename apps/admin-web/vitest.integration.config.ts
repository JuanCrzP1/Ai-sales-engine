import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

/**
 * Pruebas de integración: la interfaz real contra la API real, BusinessConfig v1 y una base SQLite temporal. Necesitan el
 * entorno de Python del proyecto, pero ningún servicio externo. Se ejecutan con `npm run test:integration`.
 */
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    include: ["src/test/integration/**/*.test.{ts,tsx}"],
    testTimeout: 180_000,
    hookTimeout: 180_000,
    fsModuleCache: false,
  },
});
