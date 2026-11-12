import type { Help, HelpArticleSummary } from "../../repositories/help";
import type { HttpClient } from "./httpClient";

interface SummaryPayload {
  slug: string;
  module: string;
  title: string;
  summary: string;
  minutes: number;
  updated: string;
}

interface ArticlePayload extends SummaryPayload {
  module_name: string;
  body: string;
  sections: { id: string; title: string }[];
  related: SummaryPayload[];
}

const toSummary = (payload: SummaryPayload): HelpArticleSummary => ({
  slug: payload.slug,
  module: payload.module,
  title: payload.title,
  summary: payload.summary,
  minutes: payload.minutes,
  updated: payload.updated,
});

/** `Help` sobre la API del panel: `/api/help`. */
export function createApiHelp(http: HttpClient): Help {
  return {
    index: async () => {
      const payload = await http.get<{ modules: { id: string; name: string; description: string; articles: SummaryPayload[] }[] }>("/help");
      return payload.modules.map((module) => ({ id: module.id, name: module.name, description: module.description, articles: module.articles.map(toSummary) }));
    },
    search: async (query) => {
      const payload = await http.get<{ results: SummaryPayload[] }>(`/help/search?q=${encodeURIComponent(query)}`);
      return payload.results.map(toSummary);
    },
    article: async (slug) => {
      const payload = await http.get<ArticlePayload>(`/help/articles/${encodeURIComponent(slug)}`);
      return { ...toSummary(payload), moduleName: payload.module_name, body: payload.body, sections: payload.sections, related: payload.related.map(toSummary) };
    },
  };
}
