import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import type { ConversationThread } from "../domain/inbox/types";
import { createMemoryBackend, createMemoryInbox, createMemoryIntegrations, createTestServices } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

const CAFE = SAMPLE_DOCUMENT.tenant_slug;

async function open(path: string, integrations = createMemoryIntegrations()) {
  window.history.pushState({}, "", `/negocios/${CAFE}/${path}`);
  const user = userEvent.setup();
  render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { createIntegrations: () => integrations })} />);
  // Espera contenido real: sin pantallas de carga y con el título de la página.
  await waitFor(() => {
    expect(screen.queryByText(/Abriendo tu panel…|Cargando/)).not.toBeInTheDocument();
    expect(screen.getAllByRole("heading", { level: 1 }).length).toBeGreaterThan(0);
  });
  return { user, integrations };
}

describe("Integraciones", () => {
  it("tiene su lugar en el menú y es un catálogo: lo activo arriba, lo disponible y lo que llega pronto", async () => {
    await open("integraciones");
    const nav = screen.getByRole("navigation", { name: "Menú del negocio" });
    expect(within(nav).getByRole("link", { name: /^Integraciones/ })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("heading", { level: 1, name: "Integraciones" })).toBeInTheDocument();
    const groups = screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent);
    expect(groups).toEqual(["Disponibles 3", "Próximamente 4"]);
    const names = (group: string) =>
      within(screen.getByRole("region", { name: new RegExp(`^${group}`) })).getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    expect(names("Disponibles")).toEqual(["OpenRouter", "API del asistente", "Claves de API"]);
    expect(names("Próximamente")).toEqual(["Agentes de IA (MCP)", "OpenAI", "Anthropic", "Google Gemini"]);
    expect(screen.getByRole("link", { name: "Configurar API del asistente" })).toHaveAttribute("href", `/negocios/${CAFE}/integraciones/api`);
    expect(screen.getByRole("link", { name: "Configurar OpenRouter" })).toHaveAttribute("href", `/negocios/${CAFE}/configuracion/inteligencia-artificial`);
    expect(screen.queryByRole("link", { name: /OpenAI/ })).not.toBeInTheDocument();
  });

  it("filtra por categoría (y lo recuerda en la dirección) y busca sin importar las tildes", async () => {
    const integrations = createMemoryIntegrations();
    await integrations.createKey("Mi web", ["assistant:chat"]);
    integrations.state.keys[0]!.lastUsedAt = new Date(Date.now() - 5 * 60_000).toISOString();
    const { user } = await open("integraciones", integrations);
    expect(screen.getByText("En uso · usada hace 5 min")).toBeInTheDocument();
    expect(screen.getByText("1 clave activa")).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Seguridad" }));
    expect(window.location.search).toBe("?categoria=security");
    expect(screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent)).toEqual(["Claves de API"]);
    await user.click(screen.getByRole("tab", { name: "Todas" }));
    await user.type(screen.getByRole("searchbox", { name: "Buscar integración" }), "inteligencia");
    expect(screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent)).toEqual(["OpenRouter", "OpenAI", "Anthropic", "Google Gemini"]);
    await user.clear(screen.getByRole("searchbox", { name: "Buscar integración" }));
    await user.type(screen.getByRole("searchbox", { name: "Buscar integración" }), "zapier");
    expect(screen.getByText("Ninguna integración coincide")).toBeInTheDocument();
  });

  it("crea la clave, la muestra una sola vez y queda activa", async () => {
    const { user, integrations } = await open("integraciones/api");
    await user.click(screen.getByRole("button", { name: "Crear clave" }));
    const form = screen.getByRole("dialog", { name: "Crear una clave de API" });
    expect(within(form).getByLabelText(/^Nombre/)).toHaveValue("");
    await user.type(within(form).getByLabelText(/^Nombre/), "Leona");
    expect(within(form).getByRole("checkbox", { name: "Conversar con el asistente" })).toBeChecked();
    await user.click(within(form).getByRole("button", { name: "Crear clave" }));

    const shown = await screen.findByRole("dialog", { name: "Clave «Leona» creada" });
    const secret = integrations.state.secrets.get("clave-1")!;
    expect(within(shown).getByText(secret)).toBeInTheDocument();
    expect(within(shown).getByText("Cópiala ahora: no se volverá a mostrar.")).toBeInTheDocument();
    await user.click(within(shown).getByRole("button", { name: "Ya la copié" }));
    expect(screen.queryByText(secret)).not.toBeInTheDocument();
    expect(await screen.findByText(`${integrations.state.keys[0]!.prefix}…`)).toBeInTheDocument();
    expect(screen.getByText("Lista · todavía sin usar")).toBeInTheDocument();
  });

  it("explica cómo funciona y da los datos de conexión sin hablar de una plataforma en particular", async () => {
    await open("integraciones/api");
    expect(screen.getByRole("list", { name: "El recorrido de cada mensaje" })).toBeInTheDocument();
    const connection = screen.getByRole("heading", { name: "1. Tus datos de conexión" }).closest("section") as HTMLElement;
    expect(within(connection).getByText("https://motor.example.com/api/v1/assistant/messages")).toBeInTheDocument();
    expect(within(connection).queryByText(/Leona/)).not.toBeInTheDocument();
    expect(screen.getByText("Sin clave")).toBeInTheDocument();
  });

  it("guía a Leona con el flujo que conversa y sus variables reales, marcada como probada", async () => {
    await open("integraciones/api");
    const tabs = screen.getByRole("tablist", { name: "Plataforma" });
    expect(within(tabs).getAllByRole("tab").map((tab) => tab.textContent)).toEqual(["Leona Probado", "Otra plataforma", "Desarrolladores"]);
    expect(within(tabs).getByRole("tab", { name: /Leona/ })).toHaveAttribute("aria-selected", "true");
    const panel = screen.getByRole("tabpanel");
    expect(within(panel).getByText('{"contact": {"id": "{phone_number}", "name": "{full_name}"}, "message": "{ase_mensaje}"}')).toBeInTheDocument();
    expect(within(panel).getByText(/vuelva a la Integración HTTP/)).toBeInTheDocument();
    expect(within(panel).getByText("Pruébalo disparando el flujo a tu número.")).toBeInTheDocument();
  });

  it("muestra las cabeceras de la petición como nombre y valor, listas para copiar, en los datos y en cada guía", async () => {
    const { user } = await open("integraciones/api");
    const connection = screen.getByRole("heading", { name: "1. Tus datos de conexión" }).closest("section") as HTMLElement;
    const headers = (where: HTMLElement) =>
      within(within(where).getByRole("table")).getAllByRole("row").slice(1).map((row) => within(row).getAllByRole("cell").map((cell) => cell.querySelector("code")?.textContent));
    expect(headers(connection)).toEqual([["Authorization", "Bearer TU_CLAVE"], ["Content-Type", "application/json"]]);
    expect(within(connection).getByText(/Cambia TU_CLAVE por tu clave/)).toBeInTheDocument();
    expect(headers(screen.getByRole("tabpanel"))).toEqual([["Authorization", "Bearer TU_CLAVE"], ["Content-Type", "application/json"]]);
    await user.click(screen.getByRole("tab", { name: "Otra plataforma" }));
    expect(headers(screen.getByRole("tabpanel"))).toHaveLength(2);
  });

  it("para otra plataforma dice qué mandar y avisa de las variables sin reemplazar", async () => {
    const { user } = await open("integraciones/api");
    await user.click(screen.getByRole("tab", { name: "Otra plataforma" }));
    const panel = screen.getByRole("tabpanel");
    expect(within(panel).getByText('{"contact": {"id": "573001112233", "name": "Laura"}, "message": "Hola, ¿qué precios tienen?"}')).toBeInTheDocument();
    expect(within(panel).getByText("Usa las variables de tu plataforma con su nombre exacto.")).toBeInTheDocument();
    expect(within(panel).queryByText(/Leona/)).not.toBeInTheDocument();
  });

  it("a quien programa le da el ejemplo en cURL, JavaScript y Python, y se recorre con el teclado", async () => {
    const { user } = await open("integraciones/api");
    screen.getByRole("tab", { name: /Leona/ }).focus();
    await user.keyboard("{End}");
    expect(screen.getByRole("tab", { name: "Desarrolladores" })).toHaveFocus();
    expect(screen.getByRole("tab", { name: "Desarrolladores" })).toHaveAttribute("aria-selected", "true");
    const panel = screen.getByRole("tabpanel");
    expect(within(panel).getByText(/curl -X POST "https:\/\/motor\.example\.com\/api\/v1\/assistant\/messages"/)).toBeInTheDocument();
    await user.click(within(panel).getByRole("radio", { name: "Python" }));
    expect(within(panel).getByText(/requests\.post\(/)).toBeInTheDocument();
    await user.click(within(panel).getByRole("radio", { name: "JavaScript" }));
    expect(within(panel).getByText(/await fetch\(/)).toBeInTheDocument();
  });

  it("dice si una plataforma ya la está usando", async () => {
    const integrations = createMemoryIntegrations();
    const created = await integrations.createKey("Leona", ["assistant:chat"]);
    integrations.state.keys[0]!.lastUsedAt = new Date(Date.now() - 2 * 60_000).toISOString();
    await open("integraciones/api", integrations);
    expect(screen.getByText(/Conectada · usada hace 2 min/)).toBeInTheDocument();
    expect(screen.getByText(`${created.key.prefix}…`)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ver claves" })).toHaveAttribute("href", `/negocios/${CAFE}/integraciones/claves`);
  });

  it("deja probarla con lo publicado", async () => {
    const { user, integrations } = await open("integraciones/api");
    const message = screen.getByLabelText("Mensaje del cliente");
    await user.clear(message);
    await user.type(message, "¿Tienen domicilio?");
    await user.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText("Respuesta a: ¿Tienen domicilio?")).toBeInTheDocument();
    expect(screen.getByText(/"attended_by": "assistant"/)).toBeInTheDocument();
    expect(integrations.state.tried).toEqual(["¿Tienen domicilio?"]);
  });

  it("dice con honestidad cuándo todavía no hay dirección pública", async () => {
    await open("integraciones/api", createMemoryIntegrations({ url: null }));
    expect(screen.getByText("La dirección aparece cuando el motor está publicado en internet.")).toBeInTheDocument();
  });

  it("lista las claves, no muestra su valor y deja revocarlas", async () => {
    const integrations = createMemoryIntegrations();
    const created = await integrations.createKey("Leona", ["assistant:chat"]);
    const { user } = await open("integraciones/claves", integrations);
    const row = (await screen.findByText("Leona")).closest("tr") as HTMLElement;
    expect(within(row).getByText(`${created.key.prefix}…`)).toBeInTheDocument();
    expect(within(row).getByText("Conversar con el asistente")).toBeInTheDocument();
    expect(within(row).getByText("Nunca")).toBeInTheDocument();
    expect(document.body.textContent).not.toContain(created.secret);
    await user.click(within(row).getByRole("button", { name: "Revocar" }));
    await user.click(within(row).getByRole("button", { name: "Sí, revocarla" }));
    await waitFor(() => expect(within(screen.getByText("Leona").closest("tr") as HTMLElement).getByText("Revocada")).toBeInTheDocument());
    expect(integrations.state.keys[0]!.active).toBe(false);
  });

  it("un chat que llegó por la API se reconoce en la bandeja y se atiende desde la otra plataforma", async () => {
    const ago = (minutes: number) => new Date(Date.now() - minutes * 60_000).toISOString();
    const thread: ConversationThread = {
      conversation: {
        id: "c1", business: { slug: CAFE, name: "Café Aroma" }, channel: "api", contactName: "Laura", status: "open", startedAt: ago(10),
        lastMessageAt: ago(1), lastMessagePreview: "Hola", messageCount: 2, needsHuman: false, handoffRequestedAt: null, canReply: false,
      },
      messages: [],
    };
    window.history.pushState({}, "", `/negocios/${CAFE}/conversaciones?c=c1`);
    render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { inbox: createMemoryInbox([thread]) })} />);
    expect(await screen.findByText(/Llegó por la API desde otra plataforma/)).toBeInTheDocument();
    expect(screen.getAllByText(/API · Café Aroma/).length).toBeGreaterThan(0);
    // Aunque se responda allá, aquí se decide quién atiende: la IA se puede pausar y reanudar.
    expect(screen.getByRole("button", { name: /Pausar IA/ })).toBeInTheDocument();
  });
});
