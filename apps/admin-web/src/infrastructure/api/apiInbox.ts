import type {
  Author,
  BusinessActivity,
  Channel,
  ChatMessage,
  ConversationChanges,
  ConversationSummary,
  ConversationThread,
  DeliveryStatus,
  HandoffReason,
  MessageKind,
  Notification,
} from "../../domain/inbox/types";
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
  handoff_reason?: HandoffReason | null;
  ai_paused?: boolean;
  unread_count?: number;
  assistant_typing?: boolean;
  can_reply?: boolean;
  customer_waiting_since?: string | null;
  ai_resumed_at?: string | null;
}

interface ApiMessage {
  id: string;
  author: Author;
  body: string;
  intent: string | null;
  created_at: string;
  kind?: MessageKind;
  status?: DeliveryStatus;
  media?: { id: string; mime_type: string; size_bytes: number; file_name: string | null } | null;
  media_note?: string | null;
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
  kind: "handoff" | "ai_resumed";
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
  handoffReason: item.handoff_reason ?? null,
  aiPaused: item.ai_paused ?? false,
  unreadCount: item.unread_count ?? 0,
  assistantTyping: item.assistant_typing ?? false,
  canReply: item.can_reply ?? false,
  customerWaitingSince: item.customer_waiting_since ?? null,
  aiResumedAt: item.ai_resumed_at ?? null,
});

const toMessage = (item: ApiMessage): ChatMessage => ({
  id: item.id,
  author: item.author,
  body: item.body,
  intent: item.intent,
  createdAt: item.created_at,
  kind: item.kind ?? "text",
  status: item.status ?? (item.author === "customer" ? "received" : "sent"),
  media: item.media ? { id: item.media.id, mimeType: item.media.mime_type, sizeBytes: item.media.size_bytes, fileName: item.media.file_name } : null,
  mediaNote: item.media_note ?? null,
});

const path = (conversationId: string) => `/conversations/${encodeURIComponent(conversationId)}`;

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
      const payload = await http.get<{ conversation: ApiConversation; messages: ApiMessage[] }>(path(conversationId));
      return { conversation: toConversation(payload.conversation), messages: payload.messages.map(toMessage) };
    },
    live: async (conversationId, since): Promise<ConversationChanges> => {
      const query = since ? `?since=${encodeURIComponent(since)}` : "";
      const payload = await http.get<{ conversation: ApiConversation; messages: ApiMessage[]; cursor: string }>(`${path(conversationId)}/live${query}`);
      return { conversation: toConversation(payload.conversation), messages: payload.messages.map(toMessage), cursor: payload.cursor };
    },
    reply: async (conversationId, text) => toMessage(await http.post<ApiMessage>(`${path(conversationId)}/messages`, { text })),
    sendQuickReplyFile: async (conversationId, fileId, caption) =>
      toMessage(await http.post<ApiMessage>(`${path(conversationId)}/quick-reply-file`, { file_id: fileId, caption })),
    // El nombre y el texto van en encabezados (codificados como en una URL): el cuerpo es el archivo tal cual.
    sendAttachment: async (conversationId, file, caption) =>
      toMessage(await http.upload<ApiMessage>(`${path(conversationId)}/attachments`, file, { "X-File-Name": encodeURIComponent(file.name), "X-Caption": encodeURIComponent(caption) })),
    setAssistant: async (conversationId, active) => toConversation(await http.post<ApiConversation>(`${path(conversationId)}/assistant`, { active })),
    markRead: async (conversationId) => {
      await http.post(`${path(conversationId)}/read`);
    },
    media: (conversationId, mediaId) => http.blob(`${path(conversationId)}/media/${encodeURIComponent(mediaId)}`),
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
    resolveHandoff: async (conversationId) => toConversation(await http.post<ApiConversation>(`${path(conversationId)}/handoff/resolve`)),
    remove: (conversationId) => http.delete(path(conversationId)),
    removeTestChats: (slug) => http.delete(`/businesses/${encodeURIComponent(slug)}/conversations/tests`),
    notifications: async () => {
      const payload = await http.get<{ items: ApiNotification[]; unread: number }>("/notifications");
      return { items: payload.items.map(toNotification), unread: payload.unread };
    },
    markNotificationsRead: async (ids) => {
      await http.post("/notifications/read", ids ? { ids } : {});
    },
  };
}
