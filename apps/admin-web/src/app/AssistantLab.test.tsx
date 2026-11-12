import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { createMemoryAssistantLabs, createMemoryBackend, createTestServices, type MemoryAssistantLabs } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

const BUSINESS = `/negocios/${SAMPLE_DOCUMENT.tenant_slug}`;
const KEY = "sk-or-v1-clave-ficticia-de-prueba-0001";
const AI = "/configuracion/inteligencia-artificial";
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
  it("vive en Configuración, y el área de pruebas es una pestaña del Asistente IA", async () => {
    await open(AI);
    const nav = screen.getByRole("navigation", { name: "Menú del negocio" });
    expect(within(nav).getByRole("link", { name: /^Configuración/ })).toHaveAttribute("aria-current", "page");
    expect(within(screen.getByRole("navigation", { name: "Configuración" })).getByRole("link", { name: /Inteligencia artificial/ })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("heading", { level: 1, name: "Inteligencia artificial" })).toBeInTheDocument();
    cleanup();
    // La dirección de antes sigue llevando aquí.
    await open("/ia");
    expect(window.location.pathname).toBe(`${BUSINESS}${AI}`);
    cleanup();
    await open("/probar");
    expect(within(screen.getByRole("navigation", { name: "Asistente IA" })).getByRole("link", { name: "Probar" })).toHaveAttribute("aria-current", "page");
    expect(within(screen.getByRole("navigation", { name: "Menú del negocio" })).getByRole("link", { name: /^Asistente IA/ })).toHaveAttribute("aria-current", "page");
  });

  it("guarda la clave, la muestra oculta, la comprueba y deja cambiarla", async () => {
    const { user, labs } = await open(AI);
    expect(await screen.findByText("Sin clave")).toBeInTheDocument();
    expect(screen.getByText("Falta la clave")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "OpenRouter" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "OpenAI, próximamente" })).toHaveAttribute("aria-disabled", "true");

    await user.type(screen.getByLabelText(/Clave de OpenRouter/), KEY);
    await user.click(screen.getByRole("button", { name: "Mostrar contraseña" }));
    expect(screen.getByLabelText(/Clave de OpenRouter/)).toHaveAttribute("type", "text");
    await user.click(screen.getByRole("button", { name: "Guardar clave" }));

    expect(await screen.findByText("Clave guardada. El asistente de este negocio ya la usa.")).toBeInTheDocument();
    expect(labs.keys.get(SAMPLE_DOCUMENT.tenant_slug)).toBe(KEY);
    expect(screen.getByText(/^sk-or-v1-•+0001$/)).toBeInTheDocument();
    expect(screen.getByText("Conectado")).toBeInTheDocument();
    expect(document.body.textContent).not.toContain(KEY);

    await user.click(screen.getByRole("button", { name: "Comprobar la clave" }));
    expect(await screen.findByText("La clave funciona.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cambiar clave" }));
    expect(screen.getByLabelText(/Nueva clave de OpenRouter/)).toHaveValue("");
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.getByRole("button", { name: "Cambiar clave" })).toBeInTheDocument();
  });

  it("señala una clave incompleta en su campo", async () => {
    const { user } = await open(AI);
    await screen.findByText("Sin clave");
    await user.type(screen.getByLabelText(/Clave de OpenRouter/), "corta-de-mas-x");
    await user.click(screen.getByRole("button", { name: "Guardar clave" }));
    expect(await screen.findByText("Pega la clave completa de OpenRouter, sin espacios.")).toBeInTheDocument();
  });
});

describe("Probar asistente", () => {
  it("pide la clave de IA antes de conversar", async () => {
    const { user } = await open("/probar");
    await user.type(screen.getByLabelText("Mensaje de prueba"), "Hola");
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText("Este negocio todavía no tiene su clave de IA")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Agregar la clave" })).toHaveAttribute("href", `${BUSINESS}${AI}`);
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
    await open(AI, labs);
    const card = (await screen.findByRole("heading", { name: "Consumo de los últimos 30 días" })).closest("section") as HTMLElement;
    const metric = (label: string) => (within(card).getByText(label).closest(".metric") as HTMLElement).querySelector(".metric__value")?.textContent;
    await waitFor(() => expect(metric("Respuestas de la IA")).toBe("1.234"));
    expect(metric("Tokens usados")).toMatch(/^1,2\s?M/);
    expect(metric("Costo en OpenRouter")).toMatch(/USD\s?0,42/);
  });

  it("sin costo informado no lo muestra como cero", async () => {
    const labs = createMemoryAssistantLabs();
    labs.usage.set(SAMPLE_DOCUMENT.tenant_slug, { since: "2026-10-12", replies: 3, promptTokens: 900, completionTokens: 60, costUsd: null, days: [] });
    await open(AI, labs);
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

describe("Elegir el modelo", () => {
  it("se elige en una lista desplegable buscando por nombre, sin copiarlo a mano", async () => {
    const labs = createMemoryAssistantLabs();
    labs.keys.set(SAMPLE_DOCUMENT.tenant_slug, KEY);
    const { user } = await open(AI, labs);
    // Cerrada, muestra el elegido (el del sistema) con su costo.
    const trigger = await screen.findByRole("button", { name: /^Modelo GPT-4o-mini/ });
    expect(trigger).toHaveAttribute("aria-expanded", "false");
    expect(within(trigger).getByText("Del sistema")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar modelo" })).toBeDisabled();

    await user.click(trigger);
    const list = screen.getByRole("listbox", { name: "Modelos" });
    expect(within(list).getByRole("option", { name: /Predeterminado del sistema/ })).toHaveAttribute("aria-selected", "true");
    expect(within(list).getAllByText("Recomendado")).toHaveLength(2);
    expect(screen.getByRole("combobox", { name: "Buscar modelo" })).toHaveFocus();

    await user.keyboard("gemini");
    expect(within(list).getByText("1 resultado")).toBeInTheDocument();
    expect(within(list).queryByRole("option", { name: /Claude/ })).not.toBeInTheDocument();
    await user.keyboard("{Enter}");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Modelo Gemini 2.5 Flash/ })).toHaveFocus();
    await user.click(screen.getByRole("button", { name: "Guardar modelo" }));

    expect(await screen.findByText("Guardado. El asistente de este negocio ya usa este modelo.")).toBeInTheDocument();
    expect((await labs.create(SAMPLE_DOCUMENT.tenant_slug).getAISettings()).model).toBe("google/gemini-2.5-flash");
  });

  it("se cierra con Escape o al tocar afuera, sin cambiar el elegido", async () => {
    const { user } = await open(AI);
    await user.click(await screen.findByRole("button", { name: /^Modelo/ }));
    await user.keyboard("{ArrowDown}{ArrowDown}{Escape}");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Modelo GPT-4o-mini/ })).toHaveFocus();
    await user.click(screen.getByRole("button", { name: /^Modelo/ }));
    await user.click(screen.getByRole("heading", { level: 1 }));
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("muestra cuánto cuestan 1.000 respuestas y marca los gratis", async () => {
    const { user } = await open(AI);
    await user.click(await screen.findByRole("button", { name: /^Modelo/ }));
    const list = screen.getByRole("listbox", { name: "Modelos" });
    const mini = within(list).getByRole("option", { name: /GPT-4o-mini OpenAI/ });
    expect(within(mini).getByText(/USD\s?0,32 por cada 1\.000 respuestas/)).toBeInTheDocument();
    expect(within(mini).getByText("Entrada 0,15 · salida 0,60 USD por millón de tokens")).toBeInTheDocument();
    const free = within(list).getByRole("option", { name: /Llama 3.3/ });
    expect(within(free).getByText("Gratis, con límites de uso de OpenRouter")).toBeInTheDocument();
  });

  it("si la lista de OpenRouter no carga, deja escribir el modelo", async () => {
    const labs = createMemoryAssistantLabs();
    labs.catalog.current = null;
    await open(AI, labs);
    expect(await screen.findByLabelText(/Modelo/)).toHaveAttribute("placeholder", "openai/gpt-4o-mini");
    expect(screen.getByText(/No se pudo cargar la lista de OpenRouter/)).toBeInTheDocument();
  });

  it("calcula el costo de una respuesta típica y busca sin importar tildes", async () => {
    const { costPerThousandReplies, searchModels } = await import("../domain/assistant/models");
    const { SAMPLE_MODEL_CATALOG } = await import("../test/fakes");
    expect(costPerThousandReplies({ promptUsdPerMillion: 0.15, completionUsdPerMillion: 0.6 })).toBeCloseTo(0.315);
    expect(searchModels(SAMPLE_MODEL_CATALOG.models, "GÉMINI flash").map((model) => model.id)).toEqual(["google/gemini-2.5-flash"]);
    expect(searchModels(SAMPLE_MODEL_CATALOG.models, "  ")).toHaveLength(SAMPLE_MODEL_CATALOG.models.length);
  });
});
