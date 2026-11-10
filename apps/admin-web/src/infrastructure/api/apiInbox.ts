import type { Author, BusinessActivity, Channel, ChatMessage, ConversationSummary, ConversationThread, Notification } from "../../domain/inbox/types";
import type { Inbox } from "../../repositories/inbox";
import type { HttpClient } from "./httpClient";

interface ApiConversation {
  id: string;
  business: { slug: string; name: string };
  channel: Channel;
  contact_name: string | null;
  status: "open" | "closed";
  started_at: string;
  last_message_at: string;
  last_message_preview: string | null;
  message_count: number;
  needs_human: boolean;
  handoff_requested_at: string | null;
}

interface ApiMessage {
  id: string;
  author: Author;
  body: string;
  intent: string | null;
  created_at: string;
}

interface ApiActivity {
  conversations: number;
  conversations_today: number;
  messages_today: number;
  test_conversations: number;
  waiting_human: number;
}

interface ApiNotification {
  id: string;
  business: { slug: string; name: string };
  conversation_id: string | null;
  kind: "handoff";
  title: string;
  body: string | null;
  created_at: string;
  read: boolean;
}

const toNotification = (item: ApiNotification): Notification => ({
  id: item.id,
  business: item.business,
  conversationId: item.conversation_id,
  kind: item.kind,
  title: item.title,
  body: item.body,
  createdAt: item.created_at,
  read: item.read,
});

const toConversation = (item: ApiConversation): ConversationSummary => ({
  id: item.id,
  business: item.business,
  channel: item.channel,
  contactName: item.contact_name,
  status: item.status,
  startedAt: item.started_at,
  lastMessageAt: item.last_message_at,
  lastMessagePreview: item.last_message_preview,
  messageCount: item.message_count,
  needsHuman: item.needs_human,
  handoffRequestedAt: item.handoff_requested_at,
});

const toMessage = (item: ApiMessage): ChatMessage => ({ id: item.id, author: item.author, body: item.body, intent: item.intent, createdAt: item.created_at });

export function createApiInbox(http: HttpClient): Inbox {
  return {
    list: async (filter = {}) => {
      const query = new URLSearchParams();
      if (filter.business) query.set("business", filter.business);
      if (filter.channel) query.set("channel", filter.channel);
      if (filter.waitingHuman) query.set("waiting_human", "true");
      const suffix = query.toString() ? `?${query.toString()}` : "";
      return (await http.get<ApiConversation[]>(`/conversations${suffix}`)).map(toConversation);
    },
    thread: async (conversationId): Promise<ConversationThread> => {
      const payload = await http.get<{ conversation: ApiConversation; messages: ApiMessage[] }>(`/conversations/${encodeURIComponent(conversationId)}`);
      return { conversation: toConversation(payload.conversation), messages: payload.messages.map(toMessage) };
    },
    activity: async (slug): Promise<BusinessActivity> => {
      const payload = await http.get<ApiActivity>(`/businesses/${encodeURIComponent(slug)}/activity`);
      return {
        conversations: payload.conversations,
        conversationsToday: payload.conversations_today,
        messagesToday: payload.messages_today,
        testConversations: payload.test_conversations,
        waitingHuman: payload.waiting_human,
      };
    },
    resolveHandoff: async (conversationId) => toConversation(await http.post<ApiConversation>(`/conversations/${encodeURIComponent(conversationId)}/handoff/resolve`)),
    notifications: async () => {
      const payload = await http.get<{ items: ApiNotification[]; unread: number }>("/notifications");
      return { items: payload.items.map(toNotification), unread: payload.unread };
    },
    markNotificationsRead: async (ids) => {
      await http.post("/notifications/read", ids ? { ids } : {});
    },
  };
}
