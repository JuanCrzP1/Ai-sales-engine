import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { createMemoryAssistantLabs, createMemoryBackend, createTestServices, type MemoryAssistantLabs } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

const BUSINESS = `/negocios/${SAMPLE_DOCUMENT.tenant_slug}`;
const KEY = "sk-or-v1-clave-ficticia-de-prueba-0001";
const LOADING = /Abriendo tu panel…|Cargando tu configuración…|Cargando negocios…|Cargando la inteligencia artificial…/;

afterEach(cleanup);

async function open(path: string, labs: MemoryAssistantLabs = createMemoryAssistantLabs()) {
  window.history.pushState({}, "", `${BUSINESS}${path}`);
  const user = userEvent.setup({ applyAccept: false });
  render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { createAssistantLab: labs.create })} />);
  await waitFor(() => {
    expect(screen.queryByText(LOADING)).not.toBeInTheDocument();
    expect(screen.getAllByRole("heading", { level: 1 }).length).toBeGreaterThan(0);
  });
  return { user, labs };
}

describe("Inteligencia artificial", () => {
  it("aparece en el menú junto al área de pruebas", async () => {
    await open("/ia");
    const nav = screen.getByRole("navigation", { name: "Secciones de configuración" });
    expect(within(nav).getByRole("link", { name: /Inteligencia artificial/ })).toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: /Probar asistente/ })).toBeInTheDocument();
  });

  it("guarda la clave sin volver a mostrarla y la comprueba", async () => {
    const { user, labs } = await open("/ia");
    expect(await screen.findByText("Sin clave")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/Clave de OpenRouter/), KEY);
    await user.type(screen.getByLabelText(/Modelo/), "openai/gpt-4o-mini");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByText("Configurada ••••0001")).toBeInTheDocument();
    expect(labs.keys.get(SAMPLE_DOCUMENT.tenant_slug)).toBe(KEY);
    expect(screen.getByLabelText(/Nueva clave/)).toHaveValue("");
    expect(document.body.textContent).not.toContain(KEY);

    await user.click(screen.getByRole("button", { name: "Comprobar la clave" }));
    expect(await screen.findByText("La clave funciona.")).toBeInTheDocument();
  });

  it("señala una clave incompleta en su campo", async () => {
    const { user } = await open("/ia");
    await screen.findByText("Sin clave");
    await user.type(screen.getByLabelText(/Clave de OpenRouter/), "corta-de-mas-x");
    await user.click(screen.getByRole("button", { name: "Guardar" }));
    expect(await screen.findByText("Pega la clave completa de OpenRouter, sin espacios.")).toBeInTheDocument();
  });
});

describe("Probar asistente", () => {
  it("pide la clave de IA antes de conversar", async () => {
    const { user } = await open("/probar");
    await user.type(screen.getByLabelText("Mensaje de prueba"), "Hola");
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText("Este negocio todavía no tiene su clave de IA")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Agregar la clave" })).toHaveAttribute("href", `${BUSINESS}/ia`);
  });

  it("conversa, continúa la misma conversación y empieza otra", async () => {
    const labs = createMemoryAssistantLabs();
    labs.keys.set(SAMPLE_DOCUMENT.tenant_slug, KEY);
    const { user } = await open("/probar", labs);
    const input = screen.getByLabelText("Mensaje de prueba");

    await user.type(input, "Hola, ¿qué venden?");
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    const log = screen.getByRole("log", { name: "Conversación de prueba" });
    expect(await within(log).findByText("Respuesta a: Hola, ¿qué venden?")).toBeInTheDocument();
    expect(within(log).getByText("Hola, ¿qué venden?")).toBeInTheDocument();

    await user.type(input, "¿Cuánto cuesta?{Enter}");
    expect(await within(log).findByText("Respuesta a: ¿Cuánto cuesta?")).toBeInTheDocument();
    const [first, second] = labs.messages;
    expect([first?.source, second?.source]).toEqual(["draft", "draft"]);
    // El primer mensaje abre la conversación; el segundo la continúa con la que asignó el servidor.
    expect(first?.sessionId).toBeNull();
    expect(second?.sessionId).toMatch(/^[0-9a-f]{32}$/);

    await user.click(screen.getByRole("button", { name: "Nueva conversación" }));
    expect(labs.resets).toEqual([second?.sessionId]);
    expect(await within(log).findByText("Escribe el primer mensaje como lo haría un cliente.")).toBeInTheDocument();
  });

  it("prueba lo publicado en una conversación aparte", async () => {
    const labs = createMemoryAssistantLabs();
    labs.keys.set(SAMPLE_DOCUMENT.tenant_slug, KEY);
    const { user } = await open("/probar", labs);
    await user.click(screen.getByRole("radio", { name: /Lo publicado/ }));
    await user.type(screen.getByLabelText("Mensaje de prueba"), "Hola{Enter}");
    expect(await screen.findByText("Respuesta a: Hola")).toBeInTheDocument();
    expect(labs.messages).toEqual([{ slug: SAMPLE_DOCUMENT.tenant_slug, message: "Hola", source: "published", sessionId: null }]);
    expect(screen.getByText(/Respondió con la versión 1\./)).toBeInTheDocument();
  });
});
