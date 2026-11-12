import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { liveTiming } from "../domain/inbox/live";
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
    expect(links.map((link) => link.textContent?.replace(/\d+$/, "").trim())).toEqual(["Inicio", "Conversaciones", "Clientes", "Ventas", "Reportes", "Asistente IA", "Canales", "Configuración"]);
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
    // El canal va como un ícono sobre la foto, no como una etiqueta en cada chat: las etiquetas quedan para lo importante.
    expect(within(item).getByRole("img", { name: "WhatsApp" })).toBeInTheDocument();
    expect(within(item).queryByText("WhatsApp")).not.toBeInTheDocument();
    // Viendo un solo negocio, cada chat no repite de qué negocio es.
    expect(within(item).queryByText("Café Aroma")).not.toBeInTheDocument();
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


describe("Conversaciones en vivo", () => {
  const timing = { ...liveTiming };
  beforeEach(() => {
    Object.assign(liveTiming, { activeMs: 20, calmMs: 20, listMs: 30 });
    URL.createObjectURL = vi.fn(() => "blob:archivo");
    URL.revokeObjectURL = vi.fn();
  });
  afterEach(() => Object.assign(liveTiming, timing));

  const LAURA = THREADS[0]!;
  const whatsappThread = (conversation: Partial<ConversationThread["conversation"]> = {}, messages: ConversationThread["messages"] = LAURA.messages): ConversationThread => ({
    conversation: { ...LAURA.conversation, canReply: true, aiPaused: false, unreadCount: 0, ...conversation },
    messages,
  });

  async function openChat(threads: ConversationThread[]) {
    const opened = await openAt(`/negocios/${CAFE}/conversaciones`, threads);
    const list = await screen.findByRole("region", { name: "Lista de conversaciones" });
    await opened.user.click(await within(list).findByRole("button", { name: /Laura Gómez/ }));
    const thread = screen.getByRole("region", { name: "Conversación abierta" });
    await within(thread).findByRole("log", { name: "Mensajes con Laura Gómez" });
    return { ...opened, thread, list };
  }

  it("lo que escribe el cliente y el «escribiendo…» del asistente aparecen solos, sin recargar", async () => {
    const { inbox, thread } = await openChat([whatsappThread()]);
    expect(screen.getByText("En vivo")).toBeInTheDocument();
    inbox.receive("c1", { id: "m9", author: "customer", body: "¿Y tienen terraza?", intent: null, createdAt: new Date().toISOString(), kind: "text", status: "received" }, { assistantTyping: true });
    const log = within(thread).getByRole("log");
    expect(await within(log).findByText("¿Y tienen terraza?")).toBeInTheDocument();
    expect(await within(thread).findByRole("status", { name: "El asistente está escribiendo" })).toBeInTheDocument();
    inbox.update("c1", { assistantTyping: false });
    await waitFor(() => expect(within(thread).queryByRole("status", { name: "El asistente está escribiendo" })).not.toBeInTheDocument());
  });

  it("el equipo responde desde el chat y la IA queda pausada en esa conversación", async () => {
    const { user, inbox, thread } = await openChat([whatsappThread()]);
    expect(within(thread).getByText("Atiende la IA")).toBeInTheDocument();
    await user.type(within(thread).getByLabelText("Tu respuesta"), "Hola Laura, soy Juan del equipo{Enter}");
    expect(await within(within(thread).getByRole("log")).findByText("Hola Laura, soy Juan del equipo")).toBeInTheDocument();
    expect(inbox.replies).toEqual([{ conversationId: "c1", text: "Hola Laura, soy Juan del equipo" }]);
    expect(await within(thread).findByText("Atiende tu equipo")).toBeInTheDocument();
    expect(within(thread).getByLabelText("Tu respuesta")).toHaveValue("");

    await user.click(within(thread).getByRole("button", { name: /Reanudar IA/ }));
    expect(await within(thread).findByText("Atiende la IA")).toBeInTheDocument();
  });

  it("si la respuesta no sale, lo dice y el texto vuelve a la caja para intentarlo otra vez", async () => {
    const { user, inbox, thread } = await openChat([whatsappThread()]);
    inbox.failNextReply("WhatsApp no está conectado en este negocio. Conéctalo en Canales para responder desde aquí.");
    await user.type(within(thread).getByLabelText("Tu respuesta"), "¿Sigues ahí?");
    await user.click(within(thread).getByRole("button", { name: "Enviar respuesta" }));
    expect(await within(thread).findByRole("alert")).toHaveTextContent("Conéctalo en Canales");
    expect(within(thread).getByLabelText("Tu respuesta")).toHaveValue("¿Sigues ahí?");
  });

  it("los no leídos se ven en la lista y se marcan al abrir el chat", async () => {
    const opened = await openAt(`/negocios/${CAFE}/conversaciones`, [whatsappThread({ unreadCount: 3 })]);
    const list = await screen.findByRole("region", { name: "Lista de conversaciones" });
    expect(await within(list).findByLabelText("3 sin leer")).toBeInTheDocument();
    await opened.user.click(within(list).getByRole("button", { name: /Laura Gómez/ }));
    await waitFor(() => expect(opened.inbox.readMarks).toContain("c1"));
    await waitFor(() => expect(within(list).queryByLabelText("3 sin leer")).not.toBeInTheDocument());
  });

  it("muestra la foto con lo que vio la IA, la nota de voz con su transcripción y los chulos de lo que salió", async () => {
    const now = new Date().toISOString();
    const messages: ConversationThread["messages"] = [
      { id: "f1", author: "customer", body: "", intent: null, createdAt: now, kind: "image", status: "received", media: { id: "foto-1", mimeType: "image/jpeg", sizeBytes: 2048, fileName: null }, mediaNote: "Captura de una transferencia de Nequi" },
      { id: "a1", author: "customer", body: "", intent: null, createdAt: now, kind: "audio", status: "received", media: { id: "audio-1", mimeType: "audio/mpeg", sizeBytes: 4096, fileName: null }, mediaNote: "Quiero el plan básico" },
      { id: "r1", author: "assistant", body: "Ya lo reviso", intent: null, createdAt: now, kind: "text", status: "read" },
    ];
    const opened = await openAt(`/negocios/${CAFE}/conversaciones`, [whatsappThread({}, messages)]);
    opened.inbox.files.set("foto-1", new Blob(["jpeg"], { type: "image/jpeg" }));
    opened.inbox.files.set("audio-1", new Blob(["mp3"], { type: "audio/mpeg" }));
    await opened.user.click(await screen.findByRole("button", { name: /Laura Gómez/ }));
    const log = await screen.findByRole("log", { name: "Mensajes con Laura Gómez" });
    expect(await within(log).findByRole("img", { name: "Foto: Captura de una transferencia de Nequi" })).toBeInTheDocument();
    expect(within(log).getByText(/La IA vio:/)).toBeInTheDocument();
    expect(within(log).getByText(/Transcripción:/)).toBeInTheDocument();
    expect(within(log).getByText("Quiero el plan básico", { exact: false })).toBeInTheDocument();
    expect(within(log).getByRole("img", { name: "Leído" })).toBeInTheDocument();
  });

  it("dice por qué el chat pasó a una persona", async () => {
    await openChat([whatsappThread({ needsHuman: true, aiPaused: true, handoffReason: "complaint", handoffRequestedAt: minutesAgo(2) })]);
    const list = screen.getByRole("region", { name: "Lista de conversaciones" });
    expect(within(list).getByText("Tiene un reclamo")).toBeInTheDocument();
    const thread = screen.getByRole("region", { name: "Conversación abierta" });
    expect(within(thread).getByText("Tiene un reclamo")).toBeInTheDocument();
    expect(within(thread).getByText(/La IA está pausada en este chat/)).toBeInTheDocument();
  });

  it("a una conversación de prueba no se le puede responder", async () => {
    const test: ConversationThread = {
      conversation: { ...LAURA.conversation, channel: "prueba", canReply: false },
      messages: LAURA.messages,
    };
    await openChat([test]);
    expect(screen.queryByLabelText("Tu respuesta")).not.toBeInTheDocument();
    expect(screen.getByText(/No llegó a ningún cliente/)).toBeInTheDocument();
  });
});

describe("Eliminar chats", () => {
  const LAURA = THREADS[0]!;
  const testChat = (id: string, slug = CAFE): ConversationThread => ({
    conversation: { ...LAURA.conversation, id, business: { slug, name: slug }, channel: "prueba", contactName: "Prueba en el panel", canReply: false },
    messages: [{ id: `${id}-m`, author: "customer", body: "Hola", intent: null, createdAt: minutesAgo(3) }],
  });

  it("elimina un chat después de confirmar, diciendo qué se borra y que las ventas se conservan", async () => {
    const { user, inbox } = await openAt(`/negocios/${CAFE}/conversaciones`);
    const list = await screen.findByRole("region", { name: "Lista de conversaciones" });
    await user.click(await within(list).findByRole("button", { name: /Laura Gómez/ }));
    const thread = screen.getByRole("region", { name: "Conversación abierta" });

    await user.click(await within(thread).findByRole("button", { name: "Eliminar chat" }));
    const dialog = screen.getByRole("dialog", { name: "Eliminar el chat con Laura Gómez" });
    expect(within(dialog).getByText(/el asistente olvida lo que sabía de este cliente/i)).toBeInTheDocument();
    expect(within(dialog).getByText(/las ventas que registraste se conservan/i)).toBeInTheDocument();
    expect(within(dialog).getByText("Esto no se puede deshacer.")).toBeInTheDocument();

    // Cancelar no borra nada.
    await user.click(within(dialog).getByRole("button", { name: "Cancelar" }));
    expect(inbox.removed).toEqual([]);

    await user.click(within(thread).getByRole("button", { name: "Eliminar chat" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Eliminar chat" }));
    await waitFor(() => expect(within(list).queryByRole("button", { name: /Laura Gómez/ })).not.toBeInTheDocument());
    expect(inbox.removed).toEqual(["c1"]);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByText("Elige una conversación para leerla.")).toBeInTheDocument();
  });

  it("si el servidor no puede eliminarlo, lo dice y el chat sigue ahí", async () => {
    const { user, inbox } = await openAt(`/negocios/${CAFE}/conversaciones`);
    inbox.remove = async () => {
      throw new Error("sin conexión");
    };
    const list = await screen.findByRole("region", { name: "Lista de conversaciones" });
    await user.click(await within(list).findByRole("button", { name: /Laura Gómez/ }));
    await user.click(await screen.findByRole("button", { name: "Eliminar chat" }));
    const dialog = screen.getByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: "Eliminar chat" }));
    expect(await within(dialog).findByRole("alert")).toBeInTheDocument();
    expect(within(list).getByRole("button", { name: /Laura Gómez/ })).toBeInTheDocument();
  });

  it("borra de una vez los chats de «Probar asistente» del negocio, sin tocar los de clientes", async () => {
    const { user, inbox } = await openAt(`/negocios/${CAFE}/conversaciones`, [LAURA, testChat("p1"), testChat("p2"), testChat("p3", NORTE)]);
    const list = await screen.findByRole("region", { name: "Lista de conversaciones" });
    expect(await within(list).findByText(/2 chats de prueba/)).toBeInTheDocument();

    await user.click(within(list).getByRole("button", { name: /Borrar pruebas/ }));
    await user.click(within(list).getByRole("button", { name: "Sí, borrarlos" }));

    await waitFor(() => expect(within(list).queryByText(/chats de prueba/)).not.toBeInTheDocument());
    expect(inbox.removed).toEqual(["p2", "p1"]);
    expect(within(list).getByRole("button", { name: /Laura Gómez/ })).toBeInTheDocument();
  });
});
