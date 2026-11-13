import type { QuickReply, QuickReplyFile, QuickReplyInput, QuickReplyList } from "../domain/quickReplies/quickReplies";

export type { QuickReply, QuickReplyFile, QuickReplyInput, QuickReplyList, QuickReplyPiece } from "../domain/quickReplies/quickReplies";

/**
 * Las respuestas rápidas de un negocio. Los fallos se rechazan con `PersistenceError`, con un mensaje y los problemas por campo
 * (`shortcut`, `category`, `pieces[1].text`).
 */
export interface QuickReplies {
  list(): Promise<QuickReplyList>;
  create(input: QuickReplyInput): Promise<QuickReply>;
  update(id: string, input: QuickReplyInput): Promise<QuickReply>;
  remove(id: string): Promise<void>;
  /** Se usó en un chat: las más usadas salen primero. */
  markUsed(id: string): Promise<QuickReply>;
  /** Sube un archivo para usarlo en una respuesta: queda guardado con el negocio. */
  uploadFile(file: File): Promise<QuickReplyFile>;
  /** Un archivo guardado, para verlo. */
  file(fileId: string): Promise<Blob>;
}
