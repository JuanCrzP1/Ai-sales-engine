import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    // La prueba de arquitectura lista el código con import.meta.glob; con la caché persistente de
    // módulos transformados no vería archivos nuevos y podría aprobar violaciones reales.
    fsModuleCache: false,
  },
});
