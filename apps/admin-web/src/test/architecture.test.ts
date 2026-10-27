/**
 * Prueba de arquitectura: lee los imports reales del código y verifica que no haya
 * ciclos ni dependencias entre capas fuera de las permitidas (ver docs/architecture.md).
 */

const SOURCES = import.meta.glob<string>(["/src/**/*.{ts,tsx}", "!/src/**/*.test.{ts,tsx}", "!/src/test/**"], {
  query: "?raw",
  import: "default",
  eager: true,
});

/** Capa de cada archivo, por prefijo de ruta (el más específico primero). */
const LAYERS: [prefix: string, layer: string][] = [
  ["/src/components/ui/", "ui"],
  ["/src/components/brand/", "brand"],
  ["/src/components/config/", "config-ui"],
  ["/src/lib/", "lib"],
  ["/src/domain/", "domain"],
  ["/src/repositories/", "repositories"],
  ["/src/infrastructure/", "infrastructure"],
  ["/src/adapters/", "adapters"],
  ["/src/state/", "state"],
  ["/src/navigation/", "navigation"],
  ["/src/layout/", "layout"],
  ["/src/features/", "features"],
  ["/src/app/", "app"],
  ["/src/main.tsx", "main"],
];

/** Capas que cada capa puede importar (además de sí misma). */
const ALLOWED: Record<string, string[]> = {
  lib: [],
  domain: ["lib"],
  repositories: ["domain", "lib"],
  infrastructure: ["repositories", "domain", "lib"],
  adapters: ["domain", "lib"],
  ui: ["lib"],
  brand: [],
  "config-ui": ["ui", "domain", "lib", "navigation"],
  navigation: ["domain", "lib"],
  state: ["repositories", "domain", "lib"],
  layout: ["ui", "brand", "config-ui", "state", "navigation", "domain", "lib"],
  features: ["ui", "brand", "config-ui", "layout", "state", "navigation", "domain", "lib"],
  app: ["*"],
  main: ["app"],
};

function layerOf(file: string): string {
  const match = LAYERS.find(([prefix]) => file.startsWith(prefix));
  if (!match) throw new Error(`Archivo sin capa asignada: ${file}`);
  return match[1];
}

function resolveImport(from: string, specifier: string): string | null {
  const parts = from.split("/").slice(0, -1);
  for (const segment of specifier.split("/")) {
    if (segment === "..") parts.pop();
    else if (segment !== ".") parts.push(segment);
  }
  const base = parts.join("/");
  return [".ts", ".tsx", "/index.ts", "/index.tsx"].map((ext) => base + ext).find((path) => path in SOURCES) ?? null;
}

const IMPORT_PATTERN = /(?:import|export)\s[^"'`;]*?from\s+["']([^"']+)["']|import\s+["']([^"']+)["']/g;

const graph = new Map<string, string[]>(
  Object.entries(SOURCES).map(([file, source]) => [
    file,
    [...source.matchAll(IMPORT_PATTERN)]
      .map((match) => match[1] ?? match[2] ?? "")
      .filter((specifier) => specifier.startsWith("."))
      .map((specifier) => resolveImport(file, specifier))
      .filter((target): target is string => target !== null),
  ]),
);

/** Funcionalidad de un archivo dentro de features/ (p. ej. "catalog"). */
const featureOf = (file: string) => file.split("/")[3];

describe("arquitectura", () => {
  it("encuentra el código fuente", () => {
    expect(graph.size).toBeGreaterThan(50);
  });

  it("asigna una capa conocida a cada archivo", () => {
    for (const file of graph.keys()) expect(ALLOWED[layerOf(file)], file).toBeDefined();
  });

  it("respeta las dependencias permitidas entre capas", () => {
    const violations: string[] = [];
    for (const [file, targets] of graph) {
      const from = layerOf(file);
      const allowed = ALLOWED[from] ?? [];
      for (const target of targets) {
        const to = layerOf(target);
        if (to === from || allowed.includes("*") || allowed.includes(to)) continue;
        violations.push(`${file} (${from}) → ${target} (${to})`);
      }
    }
    expect(violations).toEqual([]);
  });

  it("no tiene imports entre funcionalidades distintas", () => {
    const violations = [...graph].flatMap(([file, targets]) =>
      layerOf(file) === "features"
        ? targets.filter((target) => layerOf(target) === "features" && featureOf(target) !== featureOf(file)).map((target) => `${file} → ${target}`)
        : [],
    );
    expect(violations).toEqual([]);
  });

  it("no tiene dependencias circulares", () => {
    const cycles: string[] = [];
    const state = new Map<string, "visiting" | "done">();
    const stack: string[] = [];
    const visit = (file: string) => {
      state.set(file, "visiting");
      stack.push(file);
      for (const target of graph.get(file) ?? []) {
        if (state.get(target) === "visiting") cycles.push([...stack.slice(stack.indexOf(target)), target].join(" → "));
        else if (!state.has(target)) visit(target);
      }
      stack.pop();
      state.set(file, "done");
    };
    for (const file of graph.keys()) if (!state.has(file)) visit(file);
    expect(cycles).toEqual([]);
  });
});
