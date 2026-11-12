/** La bandeja de conversaciones: los chats de cada negocio, de todos sus canales, en vivo. */

export type Channel = "whatsapp" | "instagram" | "telegram" | "web" | "prueba";
export type Author = "customer" | "assistant" | "agent";
export type MessageKind = "text" | "image" | "audio" | "video" | "document" | "sticker" | "location" | "contact" | "other";
/** Lo del cliente queda «recibido»; lo que sale pasa por enviando → enviado → entregado → leído, o «no enviado». */
export type DeliveryStatus = "received" | "sending" | "sent" | "delivered" | "read" | "failed";
/** Por qué la conversación pasó a una persona. */
export type HandoffReason = "human_request" | "complaint" | "payment_review" | "assistant";

export const HANDOFF_LABELS: Record<HandoffReason, string> = {
  human_request: "Pidió hablar con una persona",
  complaint: "Tiene un reclamo",
  payment_review: "Reportó un pago: verifícalo",
  assistant: "Necesita a una persona",
};

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
  /** Pasó a una persona y nadie del equipo la ha atendido todavía. */
  needsHuman: boolean;
  handoffRequestedAt: string | null;
  handoffReason?: HandoffReason | null;
  /** La atiende el equipo: la IA no responde en este chat hasta que la reanuden. Sin dato: la IA responde. */
  aiPaused?: boolean;
  /** Mensajes del cliente que nadie del equipo ha visto. */
  unreadCount?: number;
  /** El asistente está preparando una respuesta («escribiendo…»). */
  assistantTyping?: boolean;
  /** Se le puede responder desde el panel (el mensaje sale por su canal). */
  canReply?: boolean;
  /** Desde cuándo el cliente espera a una persona sin respuesta (la IA está pausada). */
  customerWaitingSince?: string | null;
  /** Cuándo la IA retomó sola el chat porque nadie del equipo respondió a tiempo. */
  aiResumedAt?: string | null;
}

/** Un archivo de la conversación (sin su contenido: se descarga aparte). */
export interface MediaInfo {
  id: string;
  mimeType: string;
  sizeBytes: number;
  fileName: string | null;
}

export interface ChatMessage {
  id: string;
  author: Author;
  body: string;
  intent: string | null;
  createdAt: string;
  /** Sin dato: texto. */
  kind?: MessageKind;
  status?: DeliveryStatus;
  media?: MediaInfo | null;
  /** Lo que la IA entendió de una foto o un audio: la descripción o la transcripción. */
  mediaNote?: string | null;
}

export interface ConversationThread {
  conversation: ConversationSummary;
  messages: ChatMessage[];
}

/** Lo que cambió en una conversación desde la última consulta, y la marca para la próxima (la hora del servidor). */
export interface ConversationChanges extends ConversationThread {
  cursor: string;
}

/** Lo que pasó hoy en un negocio. */
export interface BusinessActivity {
  conversations: number;
  conversationsToday: number;
  messagesToday: number;
  testConversations: number;
  waitingHuman: number;
}

/** Un aviso para el equipo: un chat pasó a una persona (`handoff`) o la IA retomó uno que nadie atendió (`ai_resumed`). `read` es de quien lo ve. */
export interface Notification {
  id: string;
  business: { slug: string; name: string };
  conversationId: string | null;
  kind: "handoff" | "ai_resumed";
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
