/**
 * Arranca la API real del panel (`scripts/run_admin_api.py`) para las pruebas de integración: base SQLite temporal, clave
 * de cifrado generada en cada ejecución y un puerto libre en 127.0.0.1. No lee `.env` ni toca la base definitiva.
 *
 * Está en JavaScript porque el proyecto no incluye los tipos de Node: el resto del panel se ejecuta en el navegador.
 */
import { spawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = process.env.ADMIN_API_ROOT ?? resolve(dirname(fileURLToPath(import.meta.url)), "../../../../..");
const STARTUP_TIMEOUT_MS = 90_000;

function pythonPath() {
  if (process.env.ADMIN_API_PYTHON) return process.env.ADMIN_API_PYTHON;
  const found = [join(REPO, ".venv", "Scripts", "python.exe"), join(REPO, ".venv", "bin", "python")].find((path) => existsSync(path));
  if (!found) throw new Error("No se encontró el Python del proyecto: define ADMIN_API_PYTHON.");
  return found;
}

function freePort() {
  return new Promise((resolvePort, reject) => {
    const probe = createServer();
    probe.once("error", reject);
    probe.listen(0, "127.0.0.1", () => {
      const { port } = probe.address();
      probe.close(() => resolvePort(port));
    });
  });
}

/** Solo lo que Python necesita para funcionar: ninguna credencial ni configuración del entorno de quien ejecuta la prueba. */
function serverEnvironment(extra) {
  const allowed = ["PATH", "Path", "SYSTEMROOT", "SystemRoot", "TEMP", "TMP", "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "WINDIR", "LANG", "LC_ALL"];
  const inherited = Object.fromEntries(allowed.filter((name) => process.env[name] !== undefined).map((name) => [name, process.env[name]]));
  return { ...inherited, PYTHONIOENCODING: "utf-8", PYTHONDONTWRITEBYTECODE: "1", ...extra };
}

export async function startApiServer() {
  const folder = mkdtempSync(join(tmpdir(), "panel-integracion-"));
  const port = await freePort();
  const apiUrl = `http://127.0.0.1:${port}/api`;
  const environment = serverEnvironment({
    ADMIN_API_PORT: String(port),
    BUSINESS_CONFIG_DATABASE_URL: `sqlite:///${join(folder, "business_config.sqlite3").replaceAll("\\", "/")}`,
    BUSINESS_CONFIG_SECRETS_KEY: `${randomBytes(32).toString("base64url")}=`,
  });
  let child = null;
  let output = "";

  async function launch() {
    child = spawn(pythonPath(), [join(REPO, "scripts", "run_admin_api.py")], { cwd: REPO, env: environment, stdio: ["ignore", "pipe", "pipe"], windowsHide: true });
    child.stdout.on("data", (chunk) => (output += chunk));
    child.stderr.on("data", (chunk) => (output += chunk));
    const started = Date.now();
    while (Date.now() - started < STARTUP_TIMEOUT_MS) {
      if (child.exitCode !== null) throw new Error(`La API terminó al arrancar:\n${output}`);
      try {
        if ((await fetch(`${apiUrl}/health`)).ok) return;
      } catch {
        // Todavía no escucha.
      }
      await new Promise((done) => setTimeout(done, 150));
    }
    throw new Error(`La API no arrancó a tiempo:\n${output}`);
  }

  /** Termina el proceso de golpe, como un corte: lo guardado debe seguir ahí. */
  function halt() {
    const running = child;
    child = null;
    if (!running || running.exitCode !== null) return Promise.resolve();
    return new Promise((done) => {
      running.once("exit", done);
      running.kill("SIGKILL");
    });
  }

  await launch();

  return {
    apiUrl,
    halt,
    start: launch,
    restart: async () => {
      await halt();
      await launch();
    },
    /** Si algún archivo de la base contiene el texto tal cual. */
    databaseContains: (text) => {
      const needle = Buffer.from(text, "utf8");
      return readdirSync(folder).some((name) => readFileSync(join(folder, name)).includes(needle));
    },
    /** Si la base existe y tiene contenido: da sentido a las comprobaciones negativas. */
    databaseSize: () => readdirSync(folder).reduce((total, name) => total + readFileSync(join(folder, name)).length, 0),
    /** Todo lo que la API escribió en sus registros, en todos sus arranques. */
    output: () => output,
    stop: async () => {
      await halt();
      rmSync(folder, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
    },
  };
}
