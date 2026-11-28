import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import type { Customer, Report, Sale } from "../domain/commerce/types";
import { MEMORY_PAYMENT_CONFIRMED, createMemoryBackend, createMemoryCommerce, createMemoryInbox, createTestServices, emptyReport } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

const CAFE = SAMPLE_DOCUMENT.tenant_slug;
const ago = (minutes: number) => new Date(Date.now() - minutes * 60_000).toISOString();

const customer = (overrides: Partial<Customer>): Customer => ({
  conversationId: "c1", name: "Laura Gómez", contact: "573001112233", channel: "whatsapp", stage: "interested", firstContactAt: ago(90),
  lastMessageAt: ago(5), messageCount: 6, needsHuman: false, purchases: 0, spent: {}, lostReason: null, ...overrides,
});

const CUSTOMERS: Customer[] = [
  customer({}),
  customer({ conversationId: "c2", name: "Pedro Ruiz", contact: "573009998877", stage: "payment", needsHuman: true }),
  customer({ conversationId: "c3", name: "Ana Mora", contact: "573004445566", stage: "customer", purchases: 1, spent: { COP: "210000.00" } }),
];

const SALE: Sale = {
  id: "v1", customerName: "Ana Mora", description: "Plan Básico", amount: "210000.00", currency: "COP", status: "confirmed",
  createdAt: ago(60), createdBy: "juan@negocio.com", conversationId: "c3",
};

async function openAt(path: string, seed: Parameters<typeof createMemoryCommerce>[0] = {}) {
  window.history.pushState({}, "", `/negocios/${CAFE}/${path}`);
  const user = userEvent.setup();
  const commerce = createMemoryCommerce(seed);
  render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { createCommerce: () => commerce })} />);
  await screen.findByRole("heading", { level: 1 });
  return { user, commerce };
}

describe("Clientes", () => {
  it("elimina un cliente con su chat después de confirmar", async () => {
    window.history.pushState({}, "", `/negocios/${CAFE}/clientes?vista=lista`);
    const user = userEvent.setup();
    const commerce = createMemoryCommerce({ customers: CUSTOMERS });
    const laura = { conversation: { id: "c1", business: { slug: CAFE, name: "Café Aroma" }, channel: "whatsapp" as const, contactName: "Laura Gómez", status: "open" as const, startedAt: ago(90), lastMessageAt: ago(5), lastMessagePreview: "Hola", messageCount: 1, needsHuman: false, handoffRequestedAt: null }, messages: [] };
    const inbox = createMemoryInbox([laura]);
    render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { createCommerce: () => commerce, inbox })} />);
    const row = (await screen.findByText("Laura Gómez")).closest("tr") as HTMLElement;

    await user.click(within(row).getByRole("button", { name: "Eliminar a Laura Gómez" }));
    const dialog = screen.getByRole("dialog", { name: "Eliminar el chat con Laura Gómez" });
    await user.click(within(dialog).getByRole("button", { name: "Eliminar chat" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(inbox.removed).toEqual(["c1"]);
  });

  it("en la lista muestra cada cliente con su etapa, filtra por etapa y busca", async () => {
    const { user } = await openAt("clientes?vista=lista", { customers: CUSTOMERS });
    const table = await screen.findByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(4);
    expect(within(table).getByText("Pagó: por verificar")).toBeInTheDocument();
    expect(within(table).getByText("$ 210.000")).toBeInTheDocument();

    await user.click(within(screen.getByRole("group", { name: "Etapas" })).getByRole("button", { name: /Pagó: por verificar/ }));
    expect(within(screen.getByRole("table")).getAllByRole("row")).toHaveLength(2);
    expect(screen.getByText("Pedro Ruiz")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Quitar filtro" }));

    await user.type(screen.getByRole("searchbox", { name: "Buscar cliente" }), "ana");
    expect(within(screen.getByRole("table")).getAllByRole("row")).toHaveLength(2);
    expect(screen.getByText("Ana Mora")).toBeInTheDocument();
  });

  it("registra una venta desde un cliente de la lista y lo pasa a «Cliente»", async () => {
    const { user, commerce } = await openAt("clientes?vista=lista", { customers: CUSTOMERS });
    const row = (await screen.findByText("Laura Gómez")).closest("tr")!;
    await user.click(within(row).getByRole("button", { name: "Registrar venta" }));
    const dialog = screen.getByRole("dialog", { name: "Registrar venta" });
    expect(within(dialog).getByLabelText(/^Cliente/)).toHaveValue("Laura Gómez");
    await user.type(within(dialog).getByLabelText(/^Qué compró/), "Plan Básico");
    await user.type(within(dialog).getByLabelText(/^Valor/), "210.000");
    await user.click(within(dialog).getByRole("button", { name: "Registrar venta" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(commerce.saleList[0]).toMatchObject({ customerName: "Laura Gómez", amount: "210000.00", currency: "COP", conversationId: "c1" });
    expect(await within((await screen.findByText("Laura Gómez")).closest("tr")!).findByText("Cliente")).toBeInTheDocument();
  });

  it("abre en el tablero: una columna por etapa con sus tarjetas y, arriba, los números del embudo", async () => {
    await openAt("clientes", { customers: CUSTOMERS, sales: [SALE] });
    const board = await screen.findByRole("group", { name: "Tablero de clientes por etapa" });
    expect(within(board).getAllByRole("region").map((column) => column.getAttribute("aria-label"))).toEqual([
      "Nuevo: 0", "Interesado: 1", "Listo para comprar: 0", "Pagó: por verificar: 1", "Cliente: 1", "No compró: 0",
    ]);
    const paid = within(board).getByRole("region", { name: "Pagó: por verificar: 1" });
    expect(within(paid).getByRole("article", { name: "Pedro Ruiz" })).toHaveTextContent("Espera a una persona");
    expect(within(board).getByRole("article", { name: "Ana Mora" })).toHaveTextContent(/Lleva .*210\.000 · 1 compra/);
    expect(within(board).getByRole("link", { name: "Abrir el chat de Laura Gómez" })).toHaveAttribute("href", `/negocios/${CAFE}/conversaciones?c=c1`);
    // Llegaron 3 a Interesado y 2 a Listo para comprar: 67 % avanza.
    expect(within(board).getByRole("region", { name: "Interesado: 1" })).toHaveTextContent("67 % avanza");

    const stats = screen.getByRole("region", { name: "Resumen del embudo" });
    expect(stats).toHaveTextContent(/En el embudo2clientes que aún no compran/);
    expect(stats).toHaveTextContent(/Vendido · 30 días.*210\.000.*1 venta/);
    expect(stats).toHaveTextContent(/De cada 100, compran33Nadie se ha perdido/);
  });

  it("mueve a un cliente con «Mover a…» y lo dice", async () => {
    const { user, commerce } = await openAt("clientes", { customers: CUSTOMERS });
    const card = await screen.findByRole("article", { name: "Laura Gómez" });
    await user.click(within(card).getByRole("button", { name: "Mover a Laura Gómez a otra etapa" }));
    const menu = screen.getByRole("menu");
    expect(within(menu).getByRole("menuitem", { name: /Interesado/ })).toBeDisabled(); // donde ya está
    await user.click(within(menu).getByRole("menuitem", { name: "Listo para comprar" }));

    expect(await screen.findByRole("status")).toHaveTextContent("Laura Gómez pasó a «Listo para comprar».");
    expect(commerce.moves).toEqual([{ conversationId: "c1", stage: "ready", reason: null }]);
    expect(within(await screen.findByRole("region", { name: "Listo para comprar: 1" })).getByRole("article", { name: "Laura Gómez" })).toBeInTheDocument();
  });

  it("al pasar a «No compró» pregunta por qué y deja el motivo en la tarjeta", async () => {
    const { user, commerce } = await openAt("clientes", { customers: CUSTOMERS });
    const card = await screen.findByRole("article", { name: "Laura Gómez" });
    await user.click(within(card).getByRole("button", { name: "Mover a Laura Gómez a otra etapa" }));
    await user.click(within(screen.getByRole("menu")).getByRole("menuitem", { name: "No compró" }));

    const dialog = screen.getByRole("dialog", { name: "¿Por qué no compró?" });
    expect(commerce.moves).toEqual([]); // todavía no se movió
    await user.click(within(dialog).getByRole("button", { name: "Le pareció caro" }));
    expect(within(dialog).getByLabelText("Motivo")).toHaveValue("Le pareció caro");
    await user.click(within(dialog).getByRole("button", { name: "Pasar a «No compró»" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(commerce.moves).toEqual([{ conversationId: "c1", stage: "lost", reason: "Le pareció caro" }]);
    expect(within(await screen.findByRole("region", { name: "No compró: 1" })).getByRole("article", { name: "Laura Gómez" })).toHaveTextContent("«Le pareció caro»");
  });

  it("a «Cliente» se pasa registrando la venta", async () => {
    const { user, commerce } = await openAt("clientes", { customers: CUSTOMERS });
    const card = await screen.findByRole("article", { name: "Pedro Ruiz" });
    await user.click(within(card).getByRole("button", { name: "Mover a Pedro Ruiz a otra etapa" }));
    await user.click(within(screen.getByRole("menu")).getByRole("menuitem", { name: /^Cliente/ }));

    const dialog = screen.getByRole("dialog", { name: "Registrar venta" });
    expect(within(dialog).getByLabelText(/^Cliente/)).toHaveValue("Pedro Ruiz");
    await user.type(within(dialog).getByLabelText(/^Qué compró/), "Plan Pro");
    await user.type(within(dialog).getByLabelText(/^Valor/), "350000");
    await user.click(within(dialog).getByRole("button", { name: "Registrar venta" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(commerce.moves).toEqual([]); // la etapa la cambia la venta, no un movimiento a mano
    expect(commerce.saleList[0]).toMatchObject({ customerName: "Pedro Ruiz", amount: "350000.00", conversationId: "c2" });
    expect(within(await screen.findByRole("region", { name: "Cliente: 2" })).getByRole("article", { name: "Pedro Ruiz" })).toBeInTheDocument();
  });

  it("arrastrar una tarjeta a otra columna la mueve", async () => {
    const { commerce } = await openAt("clientes", { customers: CUSTOMERS });
    const card = await screen.findByRole("article", { name: "Laura Gómez" });
    const target = screen.getByRole("region", { name: "Listo para comprar: 0" });
    const dataTransfer = { setData: () => undefined, effectAllowed: "" };
    fireEvent.dragStart(card, { dataTransfer });
    fireEvent.dragOver(target, { dataTransfer });
    expect(target).toHaveTextContent("Suelta aquí para pasar a Laura Gómez a «Listo para comprar»");
    fireEvent.drop(target, { dataTransfer });

    await waitFor(() => expect(commerce.moves).toEqual([{ conversationId: "c1", stage: "ready", reason: null }]));
    expect(await screen.findByRole("region", { name: "Listo para comprar: 1" })).toBeInTheDocument();
  });

  it("si una etapa tiene más clientes de los que caben, lleva a verlos en la lista", async () => {
    const more = [...CUSTOMERS, customer({ conversationId: "c4", name: "Diego Castro", contact: "573007778899", lastMessageAt: ago(50) })];
    const { user } = await openAt("clientes", { customers: more, cardsPerStage: 1 });
    const column = await screen.findByRole("region", { name: "Interesado: 2" });
    expect(within(column).getAllByRole("article")).toHaveLength(1);
    await user.click(within(column).getByRole("button", { name: "+ 1 más · ver en lista" }));

    const table = await screen.findByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(3); // el encabezado y los dos interesados
    expect(window.location.search).toBe("?vista=lista&etapa=interested");
    expect(screen.getByRole("button", { name: "Lista" })).toHaveAttribute("aria-pressed", "true");
  });

  it("busca en el tablero por nombre o teléfono", async () => {
    const { user } = await openAt("clientes", { customers: CUSTOMERS });
    await screen.findByRole("article", { name: "Laura Gómez" });
    await user.type(screen.getByRole("searchbox", { name: "Buscar cliente" }), "ana");
    await waitFor(() => expect(screen.queryByRole("article", { name: "Laura Gómez" })).not.toBeInTheDocument());
    expect(screen.getByRole("article", { name: "Ana Mora" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Interesado: 0" })).toHaveTextContent("Nadie aquí");
  });
});

describe("Ventas", () => {
  it("muestra lo vendido, los pagos por verificar y permite anular una venta", async () => {
    const { user, commerce } = await openAt("ventas", { customers: CUSTOMERS, sales: [SALE] });
    expect(await screen.findByText("Pedro Ruiz")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Pagos por verificar" })).toBeInTheDocument();
    const history = screen.getByRole("table");
    expect(within(history).getByText("Plan Básico")).toBeInTheDocument();
    expect(screen.getAllByText("$ 210.000").length).toBeGreaterThan(0);

    await user.click(within(history).getByRole("button", { name: "Anular" }));
    await user.click(within(history).getByRole("button", { name: "Sí, anular" }));
    await waitFor(() => expect(commerce.saleList[0]!.status).toBe("cancelled"));
    expect(await within(screen.getByRole("table")).findByText("Anulada")).toBeInTheDocument();
  });

  it("confirma un pago reportado: el cliente recibe el mensaje y la venta se registra; avisa en el campo si falta un dato", async () => {
    window.history.pushState({}, "", `/negocios/${CAFE}/ventas`);
    const user = userEvent.setup();
    const commerce = createMemoryCommerce({ customers: CUSTOMERS });
    const pedro = {
      conversation: {
        id: "c2", business: { slug: CAFE, name: "Café Aroma" }, channel: "whatsapp" as const, contactName: "Pedro Ruiz", status: "open" as const,
        startedAt: ago(90), lastMessageAt: ago(5), lastMessagePreview: "Ya pagué", messageCount: 1, needsHuman: true, handoffRequestedAt: ago(5),
        handoffReason: "payment_review" as const, paymentPending: true,
      },
      messages: [],
    };
    const inbox = createMemoryInbox([pedro]);
    render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { createCommerce: () => commerce, inbox })} />);
    await user.click(await screen.findByRole("button", { name: "Confirmar pago" }));
    const dialog = screen.getByRole("dialog", { name: "Confirmar pago" });
    expect(await within(dialog).findByText(MEMORY_PAYMENT_CONFIRMED)).toBeInTheDocument();
    expect(within(dialog).getByLabelText(/^Cliente/)).toHaveValue("Pedro Ruiz");

    // La venta es opcional, pero si se empieza a escribir, se completa.
    await user.type(within(dialog).getByLabelText(/^Qué compró/), "Plan Básico");
    await user.click(within(dialog).getByRole("button", { name: "Confirmar y enviar" }));
    expect(within(dialog).getByText("Escribe el valor, o deja la venta en blanco.")).toBeInTheDocument();
    expect(inbox.confirmations).toEqual([]);
    await user.type(within(dialog).getByLabelText(/^Valor/), "210.000");
    await user.click(within(dialog).getByRole("button", { name: "Confirmar y enviar" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(inbox.confirmations).toEqual([{ conversationId: "c2", sale: { customerName: "Pedro Ruiz", description: "Plan Básico", amount: "210000", currency: "COP" } }]);
    expect(screen.getByText("El cliente ya recibió tu mensaje y la venta quedó registrada.")).toBeInTheDocument();
  });
});

describe("Reportes", () => {
  const report = (): Report => {
    const base = emptyReport(30);
    base.days[base.days.length - 1] = { ...base.days.at(-1)!, newConversations: 3, sales: 1 };
    return {
      ...base,
      totals: { conversations: 12, customerMessages: 80, assistantMessages: 60, agentMessages: 20, handoffs: 2, sales: 4, revenue: { COP: "840000.00" } },
      previous: { conversations: 8, customerMessages: 50, assistantMessages: 40, agentMessages: 10, handoffs: 4, sales: 2, revenue: { COP: "420000.00" } },
      funnel: { new: 12, interested: 9, ready: 5, payment: 4, customer: 4 },
      handoffsByReason: { complaint: 1, payment_review: 1 },
      aiCostUsd: 0.42,
      aiReplies: 60,
    };
  };

  it("compara con el periodo anterior y muestra el embudo, quién respondió y por qué pasó a una persona", async () => {
    const { user, commerce } = await openAt("reportes", { report: report() });
    expect(await screen.findByText("Conversaciones nuevas")).toBeInTheDocument();
    expect(screen.getByText("$ 840.000")).toBeInTheDocument();
    expect(screen.getAllByText("▲ 100 %").length).toBeGreaterThan(0);
    expect(screen.getByText("▼ 50 %").closest(".kpi__delta")).toHaveClass("kpi__delta--good");
    expect(within(screen.getByRole("region", { name: "Embudo de ventas" })).getByText("Listo para comprar")).toBeInTheDocument();
    expect(screen.getByText("Tiene un reclamo")).toBeInTheDocument();
    expect(screen.getByText("Reportó un pago: verifícalo")).toBeInTheDocument();
    expect(screen.getByText("US$ 0,42")).toBeInTheDocument();
    expect(screen.getAllByRole("table", { hidden: true }).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "7 días" }));
    await waitFor(() => expect(commerce.reportDays).toContain(7));
  });
});
