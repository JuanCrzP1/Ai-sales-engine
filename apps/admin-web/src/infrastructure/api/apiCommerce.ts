import type { Report, ReportTotals, Sale, Stage } from "../../domain/commerce/types";
import type { Commerce } from "../../repositories/commerce";
import type { HttpClient } from "./httpClient";

interface ApiCustomer {
  conversation_id: string;
  name: string | null;
  contact: string;
  channel: string;
  stage: Stage;
  first_contact_at: string;
  last_message_at: string;
  message_count: number;
  needs_human: boolean;
  purchases: number;
  spent: Record<string, string>;
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

const toTotals = (item: ApiTotals): ReportTotals => ({
  conversations: item.conversations,
  customerMessages: item.customer_messages,
  assistantMessages: item.assistant_messages,
  agentMessages: item.agent_messages,
  handoffs: item.handoffs,
  sales: item.sales,
  revenue: item.revenue,
});

/** `Commerce` sobre la API del panel: `/api/businesses/{slug}/customers`, `/sales` y `/reports`. */
export function createApiCommerce(http: HttpClient, slug: string): Commerce {
  const base = `/businesses/${encodeURIComponent(slug)}`;
  return {
    customers: async (filter = {}) => {
      const query = new URLSearchParams();
      if (filter.stage) query.set("stage", filter.stage);
      if (filter.query?.trim()) query.set("q", filter.query.trim());
      const suffix = query.toString() ? `?${query.toString()}` : "";
      return (await http.get<ApiCustomer[]>(`${base}/customers${suffix}`)).map((item) => ({
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
      }));
    },
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
