/** La bandeja de conversaciones: los chats de cada negocio, de todos sus canales. */

export type Channel = "whatsapp" | "instagram" | "telegram" | "web" | "prueba";
export type Author = "customer" | "assistant" | "agent";

export const CHANNELS: Channel[] = ["whatsapp", "instagram", "telegram", "web", "prueba"];

export const CHANNEL_LABELS: Record<Channel, string> = {
  whatsapp: "WhatsApp",
  instagram: "Instagram",
  telegram: "Telegram",
  web: "Chat web",
  prueba: "Prueba",
};

export interface ConversationSummary {
  id: string;
  /** El negocio al que llegó el chat. */
  business: { slug: string; name: string };
  channel: Channel;
  contactName: string | null;
  status: "open" | "closed";
  startedAt: string;
  lastMessageAt: string;
  lastMessagePreview: string | null;
  messageCount: number;
  /** El asistente la pasó a una persona y nadie del equipo la ha atendido todavía. */
  needsHuman: boolean;
  handoffRequestedAt: string | null;
}

export interface ChatMessage {
  id: string;
  author: Author;
  body: string;
  intent: string | null;
  createdAt: string;
}

export interface ConversationThread {
  conversation: ConversationSummary;
  messages: ChatMessage[];
}

/** Lo que pasó hoy en un negocio. */
export interface BusinessActivity {
  conversations: number;
  conversationsToday: number;
  messagesToday: number;
  testConversations: number;
  waitingHuman: number;
}

/** Un aviso para el equipo: por ahora, que el asistente pasó una conversación a una persona. `read` es de quien lo ve. */
export interface Notification {
  id: string;
  business: { slug: string; name: string };
  conversationId: string | null;
  kind: "handoff";
  title: string;
  body: string | null;
  createdAt: string;
  read: boolean;
}

export interface NotificationFeed {
  items: Notification[];
  unread: number;
}

export interface InboxFilter {
  /** Sin negocio: todos los del usuario. */
  business?: string;
  channel?: Channel;
  /** Solo las que esperan a una persona. */
  waitingHuman?: boolean;
}
