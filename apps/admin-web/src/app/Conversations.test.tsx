import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import type { ConversationThread, Notification } from "../domain/inbox/types";
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
    conversation: { id: "c1", business: { slug: CAFE, name: "Café Aroma" }, channel: "whatsapp", contactName: "Laura Gómez", status: "open", startedAt: minutesAgo(30), lastMessageAt: minutesAgo(5), lastMessagePreview: "Te espero a las 8.", messageCount: 2, needsHuman: false, handoffRequestedAt: null },
    messages: [
      { id: "m1", author: "customer", body: "¿Tienen mesa para 4 esta noche?", intent: null, createdAt: minutesAgo(6) },
      { id: "m2", author: "assistant", body: "Te espero a las 8.", intent: "buy", createdAt: minutesAgo(5) },
    ],
  },
  {
    conversation: { id: "c2", business: { slug: NORTE, name: "Software Norte" }, channel: "telegram", contactName: null, status: "open", startedAt: minutesAgo(90), lastMessageAt: minutesAgo(60), lastMessagePreview: "¿Cuánto cuesta el plan?", messageCount: 1, needsHuman: false, handoffRequestedAt: null },
    messages: [{ id: "m3", author: "customer", body: "¿Cuánto cuesta el plan?", intent: null, createdAt: minutesAgo(60) }],
  },
];

async function openAt(path: string, threads = THREADS, notifications: Notification[] = []) {
  window.history.pushState({}, "", path);
  const user = userEvent.setup({ applyAccept: false });
  const inbox = createMemoryInbox(threads, notifications);
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
  it("los canales no se presentan como conectados: WhatsApp por conectar y los demás, próximamente", async () => {
    await openAt(`/negocios/${CAFE}/canales`);
    expect(await screen.findByText("No conectado")).toBeInTheDocument();
    expect(screen.getAllByText("Próximamente").length).toBeGreaterThanOrEqual(2);
    expect(screen.queryByText("Conectado")).not.toBeInTheDocument();
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


/** Un cliente que pidió una persona en Café Aroma, y su aviso. */
const WAITING: ConversationThread = {
  conversation: {
    id: "c9", business: { slug: CAFE, name: "Café Aroma" }, channel: "whatsapp", contactName: "Marta Ríos", status: "open",
    startedAt: minutesAgo(20), lastMessageAt: minutesAgo(2), lastMessagePreview: "Te paso con un asesor.", messageCount: 2,
    needsHuman: true, handoffRequestedAt: minutesAgo(2),
  },
  messages: [
    { id: "m9", author: "customer", body: "Quiero hablar con alguien", intent: null, createdAt: minutesAgo(3) },
    { id: "m10", author: "assistant", body: "Te paso con un asesor.", intent: "info", createdAt: minutesAgo(2) },
  ],
};
const HANDOFF_NOTICE: Notification = {
  id: "n1", business: { slug: CAFE, name: "Café Aroma" }, conversationId: "c9", kind: "handoff",
  title: "Marta Ríos pidió hablar con una persona", body: "Quiero hablar con alguien", createdAt: minutesAgo(2), read: false,
};

describe("Pasar a una persona", () => {
  it("la campana muestra los avisos sin leer y abre la conversación del aviso", async () => {
    const { user, inbox } = await openAt(`/negocios/${CAFE}`, [...THREADS, WAITING], [HANDOFF_NOTICE]);
    const bell = await screen.findByRole("button", { name: "Notificaciones: 1 sin leer" });
    await user.click(bell);
    const panel = screen.getByRole("dialog", { name: "Notificaciones" });
    await user.click(within(panel).getByRole("button", { name: /Marta Ríos pidió hablar con una persona/ }));

    expect(window.location.pathname).toBe(`/negocios/${CAFE}/conversaciones`);
    expect(window.location.search).toBe("?c=c9");
    const thread = await screen.findByRole("region", { name: "Conversación abierta" });
    expect(await within(thread).findByText("Este cliente pidió hablar con una persona")).toBeInTheDocument();
    expect(inbox.notificationList[0]?.read).toBe(true);
    await waitFor(() => expect(screen.getByRole("button", { name: "Notificaciones" })).toBeInTheDocument());
  });

  it("filtra quienes esperan a una persona y marca la conversación como atendida", async () => {
    const { user, inbox } = await openAt(`/negocios/${CAFE}/conversaciones`, [...THREADS, WAITING]);
    const list = await screen.findByRole("region", { name: "Lista de conversaciones" });
    await within(list).findByRole("button", { name: /Laura Gómez/ });
    await user.click(within(list).getByRole("button", { name: /Esperan a una persona/ }));
    await waitFor(() => expect(within(list).queryByRole("button", { name: /Laura Gómez/ })).not.toBeInTheDocument());
    expect(inbox.requests.at(-1)).toEqual({ business: CAFE, waitingHuman: true });
    const waiting = within(list).getByRole("button", { name: /Marta Ríos/ });
    expect(within(waiting).getByText("Pide una persona")).toBeInTheDocument();

    await user.click(waiting);
    const thread = screen.getByRole("region", { name: "Conversación abierta" });
    await user.click(await within(thread).findByRole("button", { name: "Ya lo atendí" }));
    expect(inbox.resolved).toEqual(["c9"]);
    await waitFor(() => expect(within(thread).queryByText("Este cliente pidió hablar con una persona")).not.toBeInTheDocument());
  });

  it("marcar todo como leído deja la campana sin pendientes", async () => {
    const { user, inbox } = await openAt(`/negocios/${CAFE}`, [...THREADS, WAITING], [HANDOFF_NOTICE, { ...HANDOFF_NOTICE, id: "n2" }]);
    await user.click(await screen.findByRole("button", { name: "Notificaciones: 2 sin leer" }));
    await user.click(screen.getByRole("button", { name: "Marcar todo como leído" }));
    expect(await screen.findByRole("button", { name: "Notificaciones" })).toBeInTheDocument();
    expect(inbox.notificationList.every((item) => item.read)).toBe(true);
  });

  it("el inicio cuenta quienes esperan a una persona", async () => {
    await openAt(`/negocios/${CAFE}`, [...THREADS, WAITING]);
    const today = screen.getByRole("region", { name: "Hoy en tu negocio" });
    const metric = (await within(today).findByText("Esperan a una persona")).closest(".metric") as HTMLElement;
    await waitFor(() => expect(within(metric).getByText("1")).toBeInTheDocument());
  });
});
