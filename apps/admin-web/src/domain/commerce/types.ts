/** Clientes, ventas y reportes de un negocio. Los valores de dinero llegan como texto con dos decimales. */

/** La etapa a la que llegó un cliente: solo avanza. */
export type Stage = "new" | "interested" | "ready" | "payment" | "customer";
export const STAGES: Stage[] = ["new", "interested", "ready", "payment", "customer"];
export const STAGE_LABELS: Record<Stage, string> = {
  new: "Nuevo",
  interested: "Interesado",
  ready: "Listo para comprar",
  payment: "Pagó: por verificar",
  customer: "Cliente",
};
export const STAGE_HINTS: Record<Stage, string> = {
  new: "Escribió, todavía sin interés claro.",
  interested: "Preguntó, contó qué necesita o dudó.",
  ready: "Quiso comprar.",
  payment: "Reportó un pago: verifícalo y registra la venta.",
  customer: "Ya compró.",
};

export interface Customer {
  conversationId: string;
  name: string | null;
  contact: string;
  channel: string;
  stage: Stage;
  firstContactAt: string;
  lastMessageAt: string;
  messageCount: number;
  needsHuman: boolean;
  purchases: number;
  /** Lo que ha comprado, por moneda. */
  spent: Record<string, string>;
}

export interface Sale {
  id: string;
  customerName: string;
  description: string;
  amount: string;
  currency: string;
  status: "confirmed" | "cancelled";
  createdAt: string;
  createdBy: string | null;
  conversationId: string | null;
}

export interface NewSale {
  customerName: string;
  description: string;
  amount: string;
  currency: string;
  conversationId?: string | null;
}

export interface ReportDay {
  day: string;
  newConversations: number;
  customerMessages: number;
  assistantMessages: number;
  agentMessages: number;
  sales: number;
}

export interface ReportTotals {
  conversations: number;
  customerMessages: number;
  assistantMessages: number;
  agentMessages: number;
  handoffs: number;
  sales: number;
  revenue: Record<string, string>;
}

export interface Report {
  since: string;
  until: string;
  days: ReportDay[];
  totals: ReportTotals;
  previous: ReportTotals;
  funnel: Record<Stage, number>;
  handoffsByReason: Record<string, number>;
  aiCostUsd: number | null;
  aiReplies: number;
}

export interface CustomerFilter {
  stage?: Stage;
  query?: string;
}

const MONEY: Record<string, Intl.NumberFormat> = {};

/** «$ 40.000» en pesos, «US$ 45,00» en dólares: como lo lee alguien en Colombia. */
export function formatMoney(amount: string | number, currency: string): string {
  const value = typeof amount === "number" ? amount : Number(amount);
  const decimals = currency === "COP" ? 0 : 2;
  MONEY[currency] ??= new Intl.NumberFormat("es-CO", { style: "currency", currency, minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  return MONEY[currency].format(Number.isFinite(value) ? value : 0);
}

/** El cambio frente al periodo anterior, en porcentaje redondeado (null si antes no había nada). */
export function change(current: number, previous: number): number | null {
  if (previous === 0) return null;
  return Math.round(((current - previous) / previous) * 100);
}
