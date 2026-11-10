import type { BusinessActivity, ConversationSummary, ConversationThread, InboxFilter } from "../domain/inbox/types";

/** La bandeja de conversaciones del usuario: solo trae chats de sus negocios. Los fallos se rechazan con `PersistenceError`. */
export interface Inbox {
  list(filter?: InboxFilter): Promise<ConversationSummary[]>;
  thread(conversationId: string): Promise<ConversationThread>;
  activity(slug: string): Promise<BusinessActivity>;
}
