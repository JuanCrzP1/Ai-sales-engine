import type { BusinessDocument, Diagnostic, PaymentFields, VersionInfo, VersionStatus } from "../../domain/config/types";
import type { ConfigRepository, ReviewReport, StoredConfig } from "../../repositories/configRepository";
import type { ApiSummary } from "./apiBusinessDirectory";
import type { HttpClient } from "./httpClient";

interface ApiVersion {
  version: number;
  status: VersionStatus;
  created_at: string | null;
  published_at: string | null;
}

interface ApiConfig extends ApiSummary {
  document: BusinessDocument | null;
  version: ApiVersion | null;
  payment_fields: PaymentFields;
}

interface ApiReview {
  version: number | null;
  diagnostics: Diagnostic[];
  compiles: boolean;
  compile_error: string | null;
}

function toVersion(payload: ApiVersion): VersionInfo {
  return { version: payload.version, status: payload.status, createdAt: payload.created_at, publishedAt: payload.published_at };
}

function toStored(payload: ApiConfig): StoredConfig {
  return {
    slug: payload.slug,
    name: payload.name,
    document: payload.document,
    version: payload.version ? toVersion(payload.version) : null,
    latestVersion: payload.latest_version,
    publishedVersion: payload.published_version,
    paymentFields: payload.payment_fields,
  };
}

export function createApiConfigRepository(http: HttpClient, slug: string): ConfigRepository {
  const base = `/businesses/${encodeURIComponent(slug)}`;
  return {
    load: async () => toStored(await http.get<ApiConfig>(`${base}/config`)),
    save: async ({ document, paymentValues, baseVersion }) =>
      toStored(await http.put<ApiConfig>(`${base}/config`, { document, payment_values: paymentValues, base_version: baseVersion })),
    review: async (): Promise<ReviewReport> => {
      const report = await http.get<ApiReview>(`${base}/review`);
      return { version: report.version, diagnostics: report.diagnostics, compiles: report.compiles, compileError: report.compile_error };
    },
    history: async () => (await http.get<ApiVersion[]>(`${base}/versions`)).map(toVersion),
    publish: async (version) => toStored(await http.post<ApiConfig>(`${base}/publish`, { version })),
    rollback: async () => toStored(await http.post<ApiConfig>(`${base}/rollback`)),
    restore: async (version) => toStored(await http.post<ApiConfig>(`${base}/versions/${version}/restore`)),
  };
}
