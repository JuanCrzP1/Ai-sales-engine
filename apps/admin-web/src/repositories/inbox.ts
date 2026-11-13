import type { BusinessActivity, ConversationChanges, ChatMessage, ConversationSummary, ConversationThread, InboxFilter, NotificationFeed } from "../domain/inbox/types";

/** La bandeja de conversaciones del usuario: solo trae chats de sus negocios. Los fallos se rechazan con `PersistenceError`. */
export interface Inbox {
  list(filter?: InboxFilter): Promise<ConversationSummary[]>;
  thread(conversationId: string): Promise<ConversationThread>;
  /** En vivo: la conversación y solo los mensajes nuevos o que cambiaron desde `since` (sin `since`, todos). */
  live(conversationId: string, since?: string): Promise<ConversationChanges>;
  /** El equipo responde: el mensaje sale por el canal del cliente y la IA se pausa en ese chat. */
  reply(conversationId: string, text: string): Promise<ChatMessage>;
  /** Envía un archivo con un texto opcional; sale por el canal del cliente y la IA se pausa. */
  sendAttachment(conversationId: string, file: File, caption: string): Promise<ChatMessage>;
  /** Envía el archivo guardado de una respuesta rápida (sale desde el servidor, sin bajarlo), con su texto ya con el nombre. */
  sendQuickReplyFile(conversationId: string, fileId: string, caption: string): Promise<ChatMessage>;
  /** Reanuda la IA en la conversación (`true`) o la pausa para atenderla el equipo (`false`). */
  setAssistant(conversationId: string, active: boolean): Promise<ConversationSummary>;
  /** Alguien del equipo abrió la conversación: no quedan mensajes sin leer. */
  markRead(conversationId: string): Promise<void>;
  /** Una foto, un audio o un documento de la conversación. */
  media(conversationId: string, mediaId: string): Promise<Blob>;
  activity(slug: string): Promise<BusinessActivity>;
  /** Alguien del equipo ya atendió a quien pidió una persona. */
  resolveHandoff(conversationId: string): Promise<ConversationSummary>;
  /**
   * Elimina el chat: sus mensajes, fotos y audios, sus avisos y lo que el asistente recuerda de ese cliente (si vuelve a escribir,
   * empieza de cero). Las ventas registradas se conservan.
   */
  remove(conversationId: string): Promise<void>;
  /** Borra de una vez los chats de «Probar asistente» del negocio. */
  removeTestChats(slug: string): Promise<void>;
  /** Los avisos de los negocios del usuario, con cuántos le faltan por leer. */
  notifications(): Promise<NotificationFeed>;
  /** Sin `ids`, marca como leídos todos los avisos de quien los ve. */
  markNotificationsRead(ids?: string[]): Promise<void>;
}
