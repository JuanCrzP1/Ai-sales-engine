import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import {
  copyShortcut,
  fillName,
  groupByCategory,
  matchQuickReplies,
  normalizeShortcut,
  slashQuery,
  UNCATEGORIZED,
} from "../domain/quickReplies/quickReplies";
import type { ConversationThread } from "../domain/inbox/types";
import { createMemoryBackend, createMemoryInbox, createMemoryQuickReplies, createTestServices, quickReply } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

const CAFE = SAMPLE_DOCUMENT.tenant_slug;
const now = new Date().toISOString();
const PRICES = quickReply("precios", ["Hola {nombre}, el combo vale $25.000 e incluye bebida."], { category: "Precios", useCount: 4 });
const PAY = quickReply("pago", ["Puedes pagar por Nequi.", "Cuando pagues, mándame la captura."], { category: "Pagos", useCount: 1 });
const HOURS = quickReply("horario", ["Abrimos de 8 a 6."]);

describe("Reglas de las respuestas rápidas", () => {
  it("normaliza el atajo como el servidor", () => {
    expect(normalizeShortcut("  /Saludo   Inicial ")).toBe("saludo inicial");
    expect(normalizeShortcut("Crédito")).toBe("credito");
  });

  it("busca primero por atajo y después por categoría o texto, sin tildes", () => {
    const replies = [HOURS, PAY, PRICES];
    expect(matchQuickReplies(replies, "pa").map((reply) => reply.shortcut)).toEqual(["pago"]);
    expect(matchQuickReplies(replies, "/pre").map((reply) => reply.shortcut)).toEqual(["precios"]);
    expect(matchQuickReplies(replies, "nequi").map((reply) => reply.shortcut)).toEqual(["pago"]);
    expect(matchQuickReplies(replies, "").length).toBe(3);
  });

  it("agrupa por categoría con «Sin categoría» al final", () => {
    expect(groupByCategory([HOURS, PRICES, PAY]).map((group) => group.category)).toEqual(["Pagos", "Precios", UNCATEGORIZED]);
  });

  it("cambia {nombre} por el primer nombre o lo quita con su espacio", () => {
    expect(fillName("Hola {nombre}, ¿cómo vas?", "laura gómez")).toBe("Hola Laura, ¿cómo vas?");
    expect(fillName("Hola {nombre}, ¿cómo vas?", null)).toBe("Hola, ¿cómo vas?");
  });

  it("solo busca con «/» al empezar el mensaje y antes de un salto de línea", () => {
    expect(slashQuery("/prec")).toBe("prec");
    expect(slashQuery("/")).toBe("");
    expect(slashQuery("hola /prec")).toBeNull();
    expect(slashQuery("/prec\nhola")).toBeNull();
  });

  it("propone un atajo libre para la copia", () => {
    expect(copyShortcut("saludo", ["saludo"])).toBe("saludo-copia");
    expect(copyShortcut("saludo", ["saludo", "saludo-copia"])).toBe("saludo-copia-2");
  });
});

async function openSettings(quick = createMemoryQuickReplies()) {
  window.history.pushState({}, "", `/negocios/${CAFE}/configuracion/respuestas-rapidas`);
  const user = userEvent.setup();
  render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { createQuickReplies: () => quick })} />);
  await screen.findByRole("heading", { level: 1, name: "Respuestas rápidas" });
  return { user, quick };
}

describe("Configuración → Respuestas rápidas", () => {
  it("ya no dice «Pronto» y explica cómo empezar", async () => {
    const { user, quick } = await openSettings();
    const tabs = screen.getByRole("navigation", { name: "Configuración" });
    expect(within(tabs).getByRole("link", { name: /Respuestas rápidas/ })).not.toHaveTextContent("Pronto");
    expect(await screen.findByText("Responde en segundos, sin copiar y pegar")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Crear la primera" }));
    const dialog = screen.getByRole("dialog", { name: "Nueva respuesta rápida" });
    await user.type(within(dialog).getByLabelText(/^Atajo/), "/Precios");
    await user.type(within(dialog).getByLabelText(/^Categoría/), "precios");
    await user.type(within(dialog).getByLabelText(/^Mensaje/), "Hola ");
    await user.click(within(dialog).getByRole("button", { name: "Agregar el nombre del cliente al mensaje 1" }));
    await user.type(within(dialog).getByLabelText(/^Mensaje/), ", el combo vale $25.000.");
    // La vista previa muestra cómo le llega a un cliente.
    expect(within(dialog).getByText("Hola María, el combo vale $25.000.")).toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "Crear respuesta" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(quick.replies).toEqual([expect.objectContaining({ shortcut: "precios", category: "Precios", pieces: [{ kind: "text", text: "Hola {nombre}, el combo vale $25.000." }] })]);
    const group = screen.getByRole("region", { name: "Precios" });
    expect(within(group).getByText("/precios")).toBeInTheDocument();
    expect(within(group).getByText("Sin usar aún")).toBeInTheDocument();
  });

  it("guarda varios mensajes en orden y muestra en su campo lo que está mal", async () => {
    const { user, quick } = await openSettings(createMemoryQuickReplies([PRICES]));
    await user.click(await screen.findByRole("button", { name: /Nueva respuesta/ }));
    const dialog = screen.getByRole("dialog", { name: "Nueva respuesta rápida" });
    await user.type(within(dialog).getByLabelText(/^Atajo/), "precios");
    await user.type(within(dialog).getByLabelText(/^Mensaje/), "Primero");
    await user.click(within(dialog).getByRole("button", { name: /Agregar otro mensaje/ }));
    await user.click(within(dialog).getByRole("button", { name: "Crear respuesta" }));
    expect(await within(dialog).findByText("Ya tienes una respuesta rápida con ese atajo. Usa otro.")).toBeInTheDocument();
    expect(within(dialog).getByText("El mensaje 2 está vacío: escríbelo o quítalo.")).toBeInTheDocument();

    await user.clear(within(dialog).getByLabelText(/^Atajo/));
    await user.type(within(dialog).getByLabelText(/^Atajo/), "bienvenida");
    await user.type(within(dialog).getByLabelText(/^Mensaje 2/), "Segundo");
    await user.click(within(dialog).getByRole("button", { name: "Subir el mensaje 2" }));
    await user.click(within(dialog).getByRole("button", { name: "Crear respuesta" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(quick.replies.find((reply) => reply.shortcut === "bienvenida")?.pieces.map((piece) => piece.text)).toEqual(["Segundo", "Primero"]);
    expect(screen.getByText("2 mensajes")).toBeInTheDocument();
  });

  it("edita, duplica con un atajo libre y borra con confirmación", async () => {
    const { user, quick } = await openSettings(createMemoryQuickReplies([PRICES, HOURS]));
    expect(await screen.findByText("Usada 4 veces")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Editar /horario" }));
    const edit = screen.getByRole("dialog", { name: "Editar /horario" });
    await user.clear(within(edit).getByLabelText(/^Mensaje/));
    await user.type(within(edit).getByLabelText(/^Mensaje/), "Abrimos de 7 a 7.");
    await user.click(within(edit).getByRole("button", { name: "Guardar cambios" }));
    await waitFor(() => expect(quick.replies.find((reply) => reply.shortcut === "horario")?.pieces[0]?.text).toBe("Abrimos de 7 a 7."));

    await user.click(screen.getByRole("button", { name: "Duplicar /precios" }));
    const copy = screen.getByRole("dialog", { name: "Duplicar respuesta rápida" });
    expect(within(copy).getByLabelText(/^Atajo/)).toHaveValue("precios-copia");
    await user.click(within(copy).getByRole("button", { name: "Crear respuesta" }));
    await waitFor(() => expect(quick.replies.map((reply) => reply.shortcut)).toContain("precios-copia"));

    await user.click(screen.getByRole("button", { name: "Borrar /horario" }));
    const confirm = screen.getByRole("dialog", { name: "¿Borrar /horario?" });
    await user.click(within(confirm).getByRole("button", { name: "Sí, borrar" }));
    await waitFor(() => expect(quick.replies.map((reply) => reply.shortcut)).not.toContain("horario"));
  });

  it("busca y filtra por categoría", async () => {
    const { user } = await openSettings(createMemoryQuickReplies([PRICES, PAY, HOURS]));
    await screen.findByText("/precios");
    await user.click(screen.getByRole("button", { name: "Pagos · 1" }));
    expect(screen.getByText("/pago")).toBeInTheDocument();
    expect(screen.queryByText("/precios")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Todas · 3" }));
    await user.type(screen.getByLabelText("Buscar respuestas rápidas"), "abrimos");
    expect(screen.getByText("/horario")).toBeInTheDocument();
    expect(screen.queryByText("/pago")).not.toBeInTheDocument();
  });

  it("quien no administra el negocio las ve pero no las cambia", async () => {
    await openSettings(createMemoryQuickReplies([PRICES], { canManage: false }));
    expect(await screen.findByText("/precios")).toBeInTheDocument();
    expect(screen.getByText(/Solo quien administra el negocio las crea y edita/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Nueva respuesta/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Editar /precios" })).not.toBeInTheDocument();
  });

  it("si no puede cargarlas lo dice y deja reintentar", async () => {
    const quick = createMemoryQuickReplies([PRICES]);
    quick.failList = true;
    const { user } = await openSettings(quick);
    expect(await screen.findByText("No se pudieron cargar las respuestas rápidas.")).toBeInTheDocument();
    quick.failList = false;
    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByText("/precios")).toBeInTheDocument();
  });
});

const LAURA: ConversationThread = {
  conversation: {
    id: "c1", business: { slug: CAFE, name: "Café Aroma" }, channel: "whatsapp", contactName: "laura gómez", status: "open", startedAt: now, lastMessageAt: now,
    lastMessagePreview: "¿Cuánto vale el combo?", messageCount: 1, needsHuman: false, handoffRequestedAt: null, canReply: true, aiPaused: false, unreadCount: 0,
  },
  messages: [{ id: "m1", author: "customer", body: "¿Cuánto vale el combo?", intent: null, createdAt: now, kind: "text", status: "received" }],
};

async function openChat(quick = createMemoryQuickReplies([PRICES, PAY, HOURS])) {
  window.history.pushState({}, "", `/negocios/${CAFE}/conversaciones`);
  const user = userEvent.setup();
  const inbox = createMemoryInbox([LAURA]);
  render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { inbox, createQuickReplies: () => quick })} />);
  const list = await screen.findByRole("region", { name: "Lista de conversaciones" });
  await user.click(await within(list).findByRole("button", { name: /laura gómez/i }));
  const thread = screen.getByRole("region", { name: "Conversación abierta" });
  await within(thread).findByRole("log");
  return { user, inbox, quick, thread };
}

describe("Respuestas rápidas en el chat", () => {
  it("con «/» se busca, Enter pone el texto con el nombre del cliente para retocarlo y cuenta el uso", async () => {
    const { user, inbox, quick, thread } = await openChat();
    const box = within(thread).getByLabelText("Tu respuesta");
    await user.type(box, "/prec");
    const picker = await within(thread).findByRole("dialog", { name: "Respuestas rápidas" });
    expect(within(picker).getAllByRole("option")).toHaveLength(1);
    await user.keyboard("{Enter}");

    expect(box).toHaveValue("Hola Laura, el combo vale $25.000 e incluye bebida.");
    expect(within(thread).queryByRole("dialog", { name: "Respuestas rápidas" })).not.toBeInTheDocument();
    await waitFor(() => expect(quick.used).toEqual(["precios"]));
    // Nada se envió todavía: se puede retocar.
    expect(inbox.replies).toEqual([]);
    await user.type(box, " ¿Te lo separo?{Enter}");
    await waitFor(() => expect(inbox.replies).toEqual([{ conversationId: "c1", text: "Hola Laura, el combo vale $25.000 e incluye bebida. ¿Te lo separo?" }]));
  });

  it("con ⚡ se busca dentro; varios mensajes quedan en espera y salen en orden", async () => {
    const { user, inbox, thread } = await openChat();
    await user.click(within(thread).getByRole("button", { name: "Respuestas rápidas" }));
    const picker = within(thread).getByRole("dialog", { name: "Respuestas rápidas" });
    // Agrupadas por categoría, las más usadas primero.
    expect(within(picker).getByText("Pagos")).toBeInTheDocument();
    await user.type(within(picker).getByLabelText("Buscar respuesta rápida"), "nequi");
    await user.click(within(picker).getByRole("button", { name: /\/pago/ }));

    const waiting = within(thread).getByRole("group", { name: "Mensajes en espera" });
    expect(within(waiting).getByText("2 mensajes en espera: salen en orden al enviar.")).toBeInTheDocument();
    await user.type(within(thread).getByLabelText("Tu respuesta"), "Gracias, Laura{Enter}");
    await waitFor(() =>
      expect(inbox.replies.map((reply) => reply.text)).toEqual(["Puedes pagar por Nequi.", "Cuando pagues, mándame la captura.", "Gracias, Laura"]),
    );
    expect(within(thread).queryByRole("group", { name: "Mensajes en espera" })).not.toBeInTheDocument();
  });

  it("si un mensaje no sale, lo que falta vuelve a la espera sin repetir lo que ya llegó", async () => {
    const { user, inbox, thread } = await openChat();
    await user.type(within(thread).getByLabelText("Tu respuesta"), "/pago{Enter}");
    inbox.failNextReply("WhatsApp no está conectado en este negocio.");
    await user.click(within(thread).getByRole("button", { name: "Enviar respuesta" }));
    expect(await within(thread).findByRole("alert")).toHaveTextContent("WhatsApp no está conectado");
    expect(within(within(thread).getByRole("group", { name: "Mensajes en espera" })).getAllByRole("listitem")).toHaveLength(2);
  });

  it("Escape cierra la búsqueda y deja el texto como estaba", async () => {
    const { user, thread } = await openChat();
    const box = within(thread).getByLabelText("Tu respuesta");
    await user.type(box, "/hor");
    expect(await within(thread).findByRole("dialog", { name: "Respuestas rápidas" })).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(within(thread).queryByRole("dialog", { name: "Respuestas rápidas" })).not.toBeInTheDocument();
    expect(box).toHaveValue("/hor");
  });

  it("sin respuestas, quien administra va directo a crearlas", async () => {
    const { user, thread } = await openChat(createMemoryQuickReplies());
    await user.type(within(thread).getByLabelText("Tu respuesta"), "/");
    const picker = await within(thread).findByRole("dialog", { name: "Respuestas rápidas" });
    expect(await within(picker).findByRole("link", { name: "Crea la primera en Configuración" })).toHaveAttribute(
      "href",
      `/negocios/${CAFE}/configuracion/respuestas-rapidas`,
    );
  });
});
