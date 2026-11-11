import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import type { Customer, Report, Sale } from "../domain/commerce/types";
import { createMemoryBackend, createMemoryCommerce, createMemoryInbox, createTestServices, emptyReport } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

const CAFE = SAMPLE_DOCUMENT.tenant_slug;
const ago = (minutes: number) => new Date(Date.now() - minutes * 60_000).toISOString();

const customer = (overrides: Partial<Customer>): Customer => ({
  conversationId: "c1", name: "Laura Gómez", contact: "573001112233", channel: "whatsapp", stage: "interested", firstContactAt: ago(90),
  lastMessageAt: ago(5), messageCount: 6, needsHuman: false, purchases: 0, spent: {}, ...overrides,
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
    window.history.pushState({}, "", `/negocios/${CAFE}/clientes`);
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

  it("muestra cada cliente con su etapa, filtra por etapa y busca", async () => {
    const { user } = await openAt("clientes", { customers: CUSTOMERS });
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

  it("registra una venta desde un cliente y lo pasa a «Cliente»", async () => {
    const { user, commerce } = await openAt("clientes", { customers: CUSTOMERS });
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

  it("confirma un pago reportado registrando su venta, y avisa en el campo si falta un dato", async () => {
    const { user, commerce } = await openAt("ventas", { customers: CUSTOMERS });
    await user.click(await screen.findByRole("button", { name: "Confirmar y registrar venta" }));
    const dialog = screen.getByRole("dialog", { name: "Registrar venta" });
    await user.click(within(dialog).getByRole("button", { name: "Registrar venta" }));
    expect(within(dialog).getByText("Escribe qué compró.")).toBeInTheDocument();
    expect(within(dialog).getByText("Escribe el valor de la venta.")).toBeInTheDocument();
    await user.type(within(dialog).getByLabelText(/^Qué compró/), "Plan Básico");
    await user.type(within(dialog).getByLabelText(/^Valor/), "210000");
    await user.click(within(dialog).getByRole("button", { name: "Registrar venta" }));
    await waitFor(() => expect(commerce.saleList).toHaveLength(1));
    expect(commerce.saleList[0]).toMatchObject({ customerName: "Pedro Ruiz", conversationId: "c2" });
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
