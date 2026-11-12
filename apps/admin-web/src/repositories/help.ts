import type { HelpArticle, HelpArticleSummary, HelpModule } from "../domain/help/help";

export type { HelpArticle, HelpArticleSummary, HelpModule } from "../domain/help/help";

/** El Centro de ayuda: los temas con sus artículos, buscar y leer uno. Es igual para todos los negocios. */
export interface Help {
  index(): Promise<HelpModule[]>;
  search(query: string): Promise<HelpArticleSummary[]>;
  /** Rechaza con `PersistenceError` (404) si el artículo no existe. */
  article(slug: string): Promise<HelpArticle>;
}
