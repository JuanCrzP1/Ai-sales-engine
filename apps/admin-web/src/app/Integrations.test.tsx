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
  it("tiene su lugar en el menú, entre Canales y Configuración, con la API, las IAs y las claves", async () => {
    await open("integraciones");
    const nav = screen.getByRole("navigation", { name: "Menú del negocio" });
    expect(within(nav).getByRole("link", { name: /^Integraciones/ })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("heading", { level: 1, name: "Integraciones" })).toBeInTheDocument();
    const names = screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent);
    expect(names).toEqual(["API del asistente", "IAs conectadas (MCP)", "Claves de API"]);
    expect(screen.getByText("Próximamente")).toBeInTheDocument();
    expect(screen.getByText("Sin conectar")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Conectar" })).toHaveAttribute("href", `/negocios/${CAFE}/integraciones/api`);
  });

  it("crea la clave, la muestra una sola vez y queda activa", async () => {
    const { user, integrations } = await open("integraciones/api");
    await user.click(screen.getByRole("button", { name: "Crear clave" }));
    const form = screen.getByRole("dialog", { name: "Crear una clave de API" });
    expect(within(form).getByLabelText(/^Nombre/)).toHaveValue("Leona");
    expect(within(form).getByRole("checkbox", { name: "Conversar con el asistente" })).toBeChecked();
    await user.click(within(form).getByRole("button", { name: "Crear clave" }));

    const shown = await screen.findByRole("dialog", { name: "Clave «Leona» creada" });
    const secret = integrations.state.secrets.get("clave-1")!;
    expect(within(shown).getByText(secret)).toBeInTheDocument();
    expect(within(shown).getByText("Cópiala ahora: no se volverá a mostrar.")).toBeInTheDocument();
    await user.click(within(shown).getByRole("button", { name: "Ya la copié" }));
    expect(screen.queryByText(secret)).not.toBeInTheDocument();
    expect(await screen.findByText(/Tienes 1 clave activa/)).toBeInTheDocument();
  });

  it("da la dirección, el ejemplo para Leona y deja probarla con lo publicado", async () => {
    const { user, integrations } = await open("integraciones/api");
    expect(screen.getByText("https://motor.example.com/api/v1/assistant/messages")).toBeInTheDocument();
    expect(screen.getByText('{"contact": {"id": "{customer.phone}", "name": "{customer.name}"}, "message": "{last_message}"}')).toBeInTheDocument();
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
