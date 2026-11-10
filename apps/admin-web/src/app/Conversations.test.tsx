import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import type { ConversationThread } from "../domain/inbox/types";
import { createMemoryBackend, createMemoryInbox, createTestServices } from "../test/fakes";
import { SAMPLE_DOCUMENT, SAMPLE_PLANS_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

const CAFE = SAMPLE_DOCUMENT.tenant_slug;
const NORTE = SAMPLE_PLANS_DOCUMENT.tenant_slug;
const LOADING = /Abriendo tu panel…|Cargando tu configuración…|Cargando conversaciones…/;
const minutesAgo = (minutes: number) => new Date(Date.now() - minutes * 60_000).toISOString();

const THREADS: ConversationThread[] = [
  {
    conversation: { id: "c1", business: { slug: CAFE, name: "Café Aroma" }, channel: "whatsapp", contactName: "Laura Gómez", status: "open", startedAt: minutesAgo(30), lastMessageAt: minutesAgo(5), lastMessagePreview: "Te espero a las 8.", messageCount: 2 },
    messages: [
      { id: "m1", author: "customer", body: "¿Tienen mesa para 4 esta noche?", intent: null, createdAt: minutesAgo(6) },
      { id: "m2", author: "assistant", body: "Te espero a las 8.", intent: "buy", createdAt: minutesAgo(5) },
    ],
  },
  {
    conversation: { id: "c2", business: { slug: NORTE, name: "Software Norte" }, channel: "telegram", contactName: null, status: "open", startedAt: minutesAgo(90), lastMessageAt: minutesAgo(60), lastMessagePreview: "¿Cuánto cuesta el plan?", messageCount: 1 },
    messages: [{ id: "m3", author: "customer", body: "¿Cuánto cuesta el plan?", intent: null, createdAt: minutesAgo(60) }],
  },
];

async function openAt(path: string, threads = THREADS) {
  window.history.pushState({}, "", path);
  const user = userEvent.setup({ applyAccept: false });
  const inbox = createMemoryInbox(threads);
  render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT, SAMPLE_PLANS_DOCUMENT]), { inbox })} />);
  await waitFor(() => {
    expect(screen.queryByText(LOADING)).not.toBeInTheDocument();
    expect(screen.getAllByRole("heading", { level: 1 }).length).toBeGreaterThan(0);
  });
  return { user, inbox };
}

describe("Menú del negocio", () => {
  it("tiene primero atender y vender, y después la configuración", async () => {
    await openAt(`/negocios/${CAFE}`);
    const links = within(screen.getByRole("navigation", { name: "Menú del negocio" })).getAllByRole("link");
    expect(links.map((link) => link.textContent?.replace(/\d+$/, "").trim())).toEqual(["Inicio", "Conversaciones", "Clientes", "Ventas", "Reportes", "Asistente IA", "Canales", "Ajustes"]);
  });

  it("el inicio muestra lo que pasó hoy en el negocio", async () => {
    await openAt(`/negocios/${CAFE}`);
    const today = screen.getByRole("region", { name: "Hoy en tu negocio" });
    expect(await within(today).findByText("Conversaciones hoy")).toBeInTheDocument();
    await waitFor(() => expect(within(today).getAllByText("1").length).toBeGreaterThan(0));
    expect(within(today).getByText("2")).toBeInTheDocument();
  });
});

describe("Conversaciones", () => {
  it("muestra los chats del negocio con su canal y su negocio, y abre el historial", async () => {
    const { user, inbox } = await openAt(`/negocios/${CAFE}/conversaciones`);
    expect(inbox.requests[0]).toEqual({ business: CAFE });
    const list = await screen.findByRole("region", { name: "Lista de conversaciones" });
    const item = await within(list).findByRole("button", { name: /Laura Gómez/ });
    expect(within(item).getByText("WhatsApp")).toBeInTheDocument();
    expect(within(item).getByText("Café Aroma")).toBeInTheDocument();
    expect(within(list).queryByText("Software Norte")).not.toBeInTheDocument();

    await user.click(item);
    const thread = screen.getByRole("region", { name: "Conversación abierta" });
    expect(await within(thread).findByRole("heading", { name: "Laura Gómez" })).toBeInTheDocument();
    expect(within(thread).getByText(/WhatsApp · Café Aroma/)).toBeInTheDocument();
    const log = within(thread).getByRole("log", { name: "Mensajes con Laura Gómez" });
    expect(within(log).getByText("¿Tienen mesa para 4 esta noche?")).toBeInTheDocument();
    expect(within(log).getByText("Te espero a las 8.")).toBeInTheDocument();
    expect(within(log).getByText("Asistente IA:")).toBeInTheDocument();
  });

  it("muestra los de todos mis negocios y filtra por canal", async () => {
    const { user } = await openAt(`/negocios/${CAFE}/conversaciones`);
    const list = await screen.findByRole("region", { name: "Lista de conversaciones" });
    await user.click(within(list).getByRole("button", { name: "Todos mis negocios" }));
    expect(await within(list).findByRole("button", { name: /Cliente de Telegram/ })).toBeInTheDocument();
    expect(within(list).getByText("Software Norte")).toBeInTheDocument();

    await user.selectOptions(within(list).getByRole("combobox"), "telegram");
    await waitFor(() => expect(within(list).queryByRole("button", { name: /Laura Gómez/ })).not.toBeInTheDocument());
    expect(within(list).getByRole("button", { name: /Cliente de Telegram/ })).toBeInTheDocument();
  });

  it("sin conversaciones explica cómo llegan", async () => {
    await openAt(`/negocios/${CAFE}/conversaciones`, []);
    expect(await screen.findByText("Aún no hay conversaciones")).toBeInTheDocument();
    expect(screen.getByText(/marcadas como Prueba/)).toBeInTheDocument();
  });
});

describe("Canales y secciones que se llenan con ellos", () => {
  it("los canales no se presentan como conectados", async () => {
    await openAt(`/negocios/${CAFE}/canales`);
    expect(screen.getAllByText("No conectado")).toHaveLength(4);
    for (const button of screen.getAllByRole("button", { name: /Conectar/ })) expect(button).toBeDisabled();
  });

  it("clientes, ventas y reportes explican qué mostrarán y llevan a conectar un canal", async () => {
    for (const [path, title] of [["clientes", "Clientes"], ["ventas", "Ventas"], ["reportes", "Reportes"]] as const) {
      await openAt(`/negocios/${CAFE}/${path}`);
      expect(screen.getByRole("heading", { level: 1, name: title })).toBeInTheDocument();
      expect(screen.getByRole("link", { name: "Conectar un canal" })).toHaveAttribute("href", `/negocios/${CAFE}/canales`);
      cleanup();
    }
  });
});
