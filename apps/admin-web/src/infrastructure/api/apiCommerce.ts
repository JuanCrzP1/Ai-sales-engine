import type { CustomerCard, CustomerEvent, CustomerNote } from "../../domain/commerce/customerCard";
import { toLabelColor, type Label } from "../../domain/commerce/labels";
import type { Pipeline } from "../../domain/commerce/pipeline";
import type { BoardStage, Customer, Report, ReportTotals, Sale, Stage } from "../../domain/commerce/types";
import type { Commerce } from "../../repositories/commerce";
import type { HttpClient } from "./httpClient";

interface ApiCustomer {
  conversation_id: string;
  name: string | null;
  contact: string;
  channel: string;
  stage: BoardStage;
  first_contact_at: string;
  last_message_at: string;
  message_count: number;
  needs_human: boolean;
  purchases: number;
  spent: Record<string, string>;
  lost_reason?: string | null;
  deal?: { amount: string; currency: string } | null;
  owner?: { user_id: string; label: string } | null;
  labels?: { id: string; name: string; color: string }[];
}

interface ApiLabel {
  id: string;
  name: string;
  color: string;
  customers: number;
}

interface ApiNote {
  id: string;
  body: string;
  author: string | null;
  created_at: string;
}

interface ApiAssignee {
  user_id: string;
  email: string | null;
  role: string;
}

interface ApiCard {
  customer: ApiCustomer;
  stage_since: string | null;
  owner: ApiAssignee | null;
  assignees: ApiAssignee[];
  purchases: ApiSale[];
  notes: ApiNote[];
  events: { id: string; kind: CustomerEvent["kind"]; source: CustomerEvent["source"]; from_stage: BoardStage | null; to_stage: BoardStage | null; detail: string | null; actor: string | null; created_at: string }[];
}

interface ApiPipeline {
  columns: { stage: BoardStage; count: number; value?: Record<string, string>; customers: ApiCustomer[] }[];
  stats: {
    open_count: number;
    open_value?: Record<string, string>;
    lost_count: number;
    won_count: number;
    won: Record<string, string>;
    close_rate: number | null;
    days_to_buy: number | null;
    advance: Partial<Record<Stage, number | null>>;
  };
}

interface ApiSale {
  id: string;
  customer_name: string;
  description: string;
  amount: string;
  currency: string;
  status: "confirmed" | "cancelled";
  created_at: string;
  created_by: string | null;
  conversation_id: string | null;
}

interface ApiTotals {
  conversations: number;
  customer_messages: number;
  assistant_messages: number;
  agent_messages: number;
  handoffs: number;
  sales: number;
  revenue: Record<string, string>;
}

interface ApiReport {
  since: string;
  until: string;
  days: { day: string; new_conversations: number; customer_messages: number; assistant_messages: number; agent_messages: number; sales: number }[];
  totals: ApiTotals;
  previous: ApiTotals;
  funnel: Record<Stage, number>;
  handoffs_by_reason: Record<string, number>;
  ai_cost_usd: number | null;
  ai_replies: number;
}

const toCustomer = (item: ApiCustomer): Customer => ({
  conversationId: item.conversation_id,
  name: item.name,
  contact: item.contact,
  channel: item.channel,
  stage: item.stage,
  firstContactAt: item.first_contact_at,
  lastMessageAt: item.last_message_at,
  messageCount: item.message_count,
  needsHuman: item.needs_human,
  purchases: item.purchases,
  spent: item.spent,
  lostReason: item.lost_reason ?? null,
  deal: item.deal ?? null,
  owner: item.owner ? { userId: item.owner.user_id, label: item.owner.label } : null,
  labels: (item.labels ?? []).map((label) => ({ id: label.id, name: label.name, color: toLabelColor(label.color) })),
});

const toLabel = (item: ApiLabel): Label => ({ id: item.id, name: item.name, color: toLabelColor(item.color), customers: item.customers });

const toNote = (item: ApiNote): CustomerNote => ({ id: item.id, body: item.body, author: item.author, createdAt: item.created_at });

const toAssignee = (item: ApiAssignee) => ({ userId: item.user_id, email: item.email, role: item.role });

const toPipeline = (item: ApiPipeline): Pipeline => ({
  columns: item.columns.map((column) => ({ stage: column.stage, count: column.count, value: column.value ?? {}, customers: column.customers.map(toCustomer) })),
  stats: {
    openCount: item.stats.open_count,
    openValue: item.stats.open_value ?? {},
    lostCount: item.stats.lost_count,
    wonCount: item.stats.won_count,
    won: item.stats.won,
    closeRate: item.stats.close_rate,
    daysToBuy: item.stats.days_to_buy,
    advance: item.stats.advance,
  },
});

const toSale = (item: ApiSale): Sale => ({
  id: item.id,
  customerName: item.customer_name,
  description: item.description,
  amount: item.amount,
  currency: item.currency,
  status: item.status,
  createdAt: item.created_at,
  createdBy: item.created_by,
  conversationId: item.conversation_id,
});

const toCard = (item: ApiCard): CustomerCard => ({
  customer: toCustomer(item.customer),
  stageSince: item.stage_since,
  owner: item.owner ? toAssignee(item.owner) : null,
  assignees: item.assignees.map(toAssignee),
  purchases: item.purchases.map(toSale),
  notes: item.notes.map(toNote),
  events: item.events.map((event) => ({
    id: event.id,
    kind: event.kind,
    source: event.source,
    fromStage: event.from_stage,
    toStage: event.to_stage,
    detail: event.detail,
    actor: event.actor,
    createdAt: event.created_at,
  })),
});

const toTotals = (item: ApiTotals): ReportTotals => ({
  conversations: item.conversations,
  customerMessages: item.customer_messages,
  assistantMessages: item.assistant_messages,
  agentMessages: item.agent_messages,
  handoffs: item.handoffs,
  sales: item.sales,
  revenue: item.revenue,
});

/** `Commerce` sobre la API del panel: `/api/businesses/{slug}/customers` (y la ficha de cada uno), `/pipeline`, `/sales` y `/reports`. */
export function createApiCommerce(http: HttpClient, slug: string): Commerce {
  const base = `/businesses/${encodeURIComponent(slug)}`;
  return {
    customers: async (filter = {}) => {
      const query = new URLSearchParams();
      if (filter.stage) query.set("stage", filter.stage);
      if (filter.query?.trim()) query.set("q", filter.query.trim());
      if (filter.label) query.set("label", filter.label);
      const suffix = query.toString() ? `?${query.toString()}` : "";
      return (await http.get<ApiCustomer[]>(`${base}/customers${suffix}`)).map(toCustomer);
    },
    pipeline: async (query = "", labelId = null) => {
      const search = new URLSearchParams();
      if (query.trim()) search.set("q", query.trim());
      if (labelId) search.set("label", labelId);
      return toPipeline(await http.get<ApiPipeline>(`${base}/pipeline${search.toString() ? `?${search.toString()}` : ""}`));
    },
    moveCustomer: async (conversationId, stage, reason) =>
      toCustomer(await http.post<ApiCustomer>(`${base}/customers/${encodeURIComponent(conversationId)}/stage`, { stage, reason: reason?.trim() || null })),
    customerCard: async (conversationId) => toCard(await http.get<ApiCard>(`${base}/customers/${encodeURIComponent(conversationId)}`)),
    updateCustomerCard: async (conversationId, change) => {
      // Solo viaja lo que cambia: un dato ausente se deja como está; vacío, se borra.
      const body: Record<string, string | null> = {};
      if (change.amount !== undefined) body.amount = change.amount;
      if (change.currency !== undefined) body.currency = change.currency;
      if (change.ownerId !== undefined) body.owner_id = change.ownerId;
      return toCard(await http.patch<ApiCard>(`${base}/customers/${encodeURIComponent(conversationId)}`, body));
    },
    addCustomerNote: async (conversationId, body) => toNote(await http.post<ApiNote>(`${base}/customers/${encodeURIComponent(conversationId)}/notes`, { body })),
    deleteCustomerNote: (conversationId, noteId) => http.delete(`${base}/customers/${encodeURIComponent(conversationId)}/notes/${encodeURIComponent(noteId)}`),
    labels: async () => (await http.get<{ labels: ApiLabel[] }>(`${base}/labels`)).labels.map(toLabel),
    createLabel: async (name, color) => toLabel(await http.post<ApiLabel>(`${base}/labels`, { name, color })),
    updateLabel: async (labelId, change) => toLabel(await http.patch<ApiLabel>(`${base}/labels/${encodeURIComponent(labelId)}`, change)),
    deleteLabel: (labelId) => http.delete(`${base}/labels/${encodeURIComponent(labelId)}`),
    setCustomerLabels: async (conversationId, labelIds) =>
      toCustomer(await http.put<ApiCustomer>(`${base}/customers/${encodeURIComponent(conversationId)}/labels`, { label_ids: labelIds })),
    sales: async (days = 90) => (await http.get<ApiSale[]>(`${base}/sales?days=${days}`)).map(toSale),
    recordSale: async (sale) =>
      toSale(
        await http.post<ApiSale>(`${base}/sales`, {
          customer_name: sale.customerName,
          description: sale.description,
          amount: sale.amount,
          currency: sale.currency,
          conversation_id: sale.conversationId ?? null,
        }),
      ),
    cancelSale: async (saleId) => toSale(await http.post<ApiSale>(`${base}/sales/${encodeURIComponent(saleId)}/cancel`)),
    report: async (days): Promise<Report> => {
      const item = await http.get<ApiReport>(`${base}/reports?days=${days}`);
      return {
        since: item.since,
        until: item.until,
        days: item.days.map((day) => ({
          day: day.day,
          newConversations: day.new_conversations,
          customerMessages: day.customer_messages,
          assistantMessages: day.assistant_messages,
          agentMessages: day.agent_messages,
          sales: day.sales,
        })),
        totals: toTotals(item.totals),
        previous: toTotals(item.previous),
        funnel: item.funnel,
        handoffsByReason: item.handoffs_by_reason,
        aiCostUsd: item.ai_cost_usd,
        aiReplies: item.ai_replies,
      };
    },
  };
}
