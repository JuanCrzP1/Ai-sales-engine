import type { ContractSchema } from "../../domain/config/contractSchema";
import type { BusinessSummary } from "../../domain/config/types";
import type { BusinessDirectory } from "../../repositories/businessDirectory";
import type { HttpClient } from "./httpClient";

export interface ApiSummary {
  slug: string;
  name: string;
  latest_version: number | null;
  draft_version: number | null;
  published_version: number | null;
}

export function toSummary(payload: ApiSummary): BusinessSummary {
  return {
    slug: payload.slug,
    name: payload.name,
    latestVersion: payload.latest_version,
    draftVersion: payload.draft_version,
    publishedVersion: payload.published_version,
  };
}

export function createApiBusinessDirectory(http: HttpClient, { local = true }: { local?: boolean } = {}): BusinessDirectory {
  return {
    canImportExisting: local,
    canRemove: local,
    list: async () => (await http.get<ApiSummary[]>("/businesses")).map(toSummary),
    create: async (input) => toSummary(await http.post<ApiSummary>("/businesses", input)),
    remove: (slug) => http.delete(`/businesses/${encodeURIComponent(slug)}?confirm=${encodeURIComponent(slug)}`),
    importExisting: () => http.post("/businesses/import"),
    contractSchema: () => http.get<ContractSchema>("/contract"),
  };
}
