import type { BusinessActivity, ConversationSummary, ConversationThread, InboxFilter, NotificationFeed } from "../domain/inbox/types";

/** La bandeja de conversaciones del usuario: solo trae chats de sus negocios. Los fallos se rechazan con `PersistenceError`. */
export interface Inbox {
  list(filter?: InboxFilter): Promise<ConversationSummary[]>;
  thread(conversationId: string): Promise<ConversationThread>;
  activity(slug: string): Promise<BusinessActivity>;
  /** Alguien del equipo ya atendió a quien pidió una persona. */
  resolveHandoff(conversationId: string): Promise<ConversationSummary>;
  /** Los avisos de los negocios del usuario, con cuántos le faltan por leer. */
  notifications(): Promise<NotificationFeed>;
  /** Sin `ids`, marca como leídos todos los avisos de quien los ve. */
  markNotificationsRead(ids?: string[]): Promise<void>;
}
