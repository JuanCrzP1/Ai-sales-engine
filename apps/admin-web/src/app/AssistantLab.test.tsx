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
  it("vive en Ajustes, y el área de pruebas es una pestaña del Asistente IA", async () => {
    await open("/ia");
    const nav = screen.getByRole("navigation", { name: "Menú del negocio" });
    expect(within(nav).getByRole("link", { name: /^Ajustes/ })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("heading", { level: 1, name: "Inteligencia artificial" })).toBeInTheDocument();
    cleanup();
    await open("/probar");
    expect(within(screen.getByRole("navigation", { name: "Asistente IA" })).getByRole("link", { name: "Probar" })).toHaveAttribute("aria-current", "page");
    expect(within(screen.getByRole("navigation", { name: "Menú del negocio" })).getByRole("link", { name: /^Asistente IA/ })).toHaveAttribute("aria-current", "page");
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

describe("Consumo de la IA", () => {
  it("muestra respuestas, tokens y costo de los últimos 30 días", async () => {
    const labs = createMemoryAssistantLabs();
    labs.usage.set(SAMPLE_DOCUMENT.tenant_slug, {
      since: "2026-10-12",
      replies: 1234,
      promptTokens: 1_100_000,
      completionTokens: 100_000,
      costUsd: 0.4231,
      days: [{ day: "2026-11-10", replies: 1234, tokens: 1_200_000 }],
    });
    await open("/ia", labs);
    const card = (await screen.findByRole("heading", { name: "Consumo de los últimos 30 días" })).closest("section") as HTMLElement;
    const metric = (label: string) => (within(card).getByText(label).closest(".metric") as HTMLElement).querySelector(".metric__value")?.textContent;
    await waitFor(() => expect(metric("Respuestas de la IA")).toBe("1.234"));
    expect(metric("Tokens usados")).toMatch(/^1,2\s?M/);
    expect(metric("Costo en OpenRouter")).toMatch(/USD\s?0,42/);
  });

  it("sin costo informado no lo muestra como cero", async () => {
    const labs = createMemoryAssistantLabs();
    labs.usage.set(SAMPLE_DOCUMENT.tenant_slug, { since: "2026-10-12", replies: 3, promptTokens: 900, completionTokens: 60, costUsd: null, days: [] });
    await open("/ia", labs);
    expect(await screen.findByText(/OpenRouter no informó el costo/)).toBeInTheDocument();
  });
});

describe("Probar asistente: lo que entendió la IA", () => {
  it("usa las mismas intenciones del motor y no inventa una que no indicó", async () => {
    const { INTENT_LABELS, intentLabel } = await import("../domain/assistant/intents");
    expect(Object.keys(INTENT_LABELS)).toEqual(["pain", "info", "objection", "buy"]);
    expect(intentLabel("buy")).toBe("Quiere comprar");
    expect([intentLabel(""), intentLabel(null), intentLabel("pricing")]).toEqual([null, null, null]);
  });
});
