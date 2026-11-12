import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { IntegrationMark } from "../../components/brand/IntegrationMark";
import { Button } from "../../components/ui/Button";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import { Tabs } from "../../components/ui/Tabs";
import { relativeTime } from "../../domain/inbox/format";
import {
  buildCatalog,
  categoryLabel,
  filterCatalog,
  groupCatalog,
  INTEGRATION_CATEGORIES,
  isCategory,
  type CatalogEntry,
  type CategoryFilter,
  type IntegrationTarget,
} from "../../domain/integrations/catalog";
import { LoadingScreen } from "../../layout/StatusScreen";
import { AGENTS_ITEM, AI_ITEM, API_KEYS_ITEM, ASSISTANT_API_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useAISettings } from "../../state/useAISettings";
import { useIntegrationsData } from "../../state/useIntegrationsData";

const TARGET_PATHS: Record<IntegrationTarget, string> = {
  "ai-settings": AI_ITEM.path,
  "assistant-api": ASSISTANT_API_ITEM.path,
  "api-keys": API_KEYS_ITEM.path,
  agents: AGENTS_ITEM.path,
};

/**
 * Integraciones: el catálogo por categorías, con buscador; lo conectado arriba («Activas»), lo que se puede conectar hoy
 * («Disponibles») y lo que llega pronto. Cada tarjeta lleva a la pantalla donde se configura.
 */
export function IntegrationsPage() {
  const data = useIntegrationsData();
  const ai = useAISettings();
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState("");
  const raw = params.get("categoria");
  const category: CategoryFilter = isCategory(raw) ? raw : "all";
  const header = (
    <PageHeader title="Integraciones" description="Conecta tu asistente con las herramientas que ya usas: la IA que lo hace responder, otras plataformas de atención y, pronto, los agentes de IA que te ayudan a administrarlo." />
  );

  // Espera también a la IA: así OpenRouter no aparece un instante «Sin conectar» antes de saber que tiene su clave.
  if (data.status === "loading" || ai.status === "loading") return <LoadingScreen label="Cargando las integraciones…" />;
  if (data.status === "error") {
    return (
      <>
        {header}
        <Alert tone="danger" title={data.error ?? "No se pudieron cargar."}>
          <Button variant="secondary" size="small" onClick={data.reload}>
            Reintentar
          </Button>
        </Alert>
      </>
    );
  }

  const catalog = buildCatalog({ keys: data.keys, aiConfigured: ai.settings ? ai.settings.key.configured : null });
  const visible = filterCatalog(catalog, category, query);
  const { active, available, soon } = groupCatalog(visible);

  const selectCategory = (next: string) => {
    const updated = new URLSearchParams(params);
    if (next === "all") updated.delete("categoria");
    else updated.set("categoria", next);
    setParams(updated, { replace: true });
  };

  return (
    <>
      {header}
      <Tabs label="Categorías" value={category} onChange={selectCategory} tabs={[{ value: "all", label: "Todas" }, ...INTEGRATION_CATEGORIES.map((item) => ({ value: item.id, label: item.label }))]}>
        <div className="integrations-hub">
          <label className="integrations-hub__search">
            <Icon name="search" size={18} />
            <input type="search" value={query} placeholder="Buscar integración…" aria-label="Buscar integración" onChange={(event) => setQuery(event.target.value)} />
          </label>
          {visible.length === 0 ? (
            <EmptyState title="Ninguna integración coincide" description="Prueba con otro nombre o elige «Todas»." />
          ) : (
            <>
              <Group title="Activas" hint="Conectadas en este negocio" entries={active} />
              <Group title="Disponibles" hint="Listas para conectar" entries={available} />
              <Group title="Próximamente" hint="En camino" entries={soon} />
            </>
          )}
        </div>
      </Tabs>
    </>
  );
}

function Group({ title, hint, entries }: { title: string; hint: string; entries: CatalogEntry[] }) {
  if (entries.length === 0) return null;
  const id = `integraciones-${title.toLowerCase()}`;
  return (
    <section className="integrations-hub__group" aria-labelledby={id}>
      <header className="integrations-hub__group-head">
        <h2 id={id}>
          {title} <span className="integrations-hub__count">{entries.length}</span>
        </h2>
        <p>{hint}</p>
      </header>
      <div className="integration-grid">
        {entries.map((entry) => (
          <IntegrationCard key={entry.id} entry={entry} />
        ))}
      </div>
    </section>
  );
}

function IntegrationCard({ entry }: { entry: CatalogEntry }) {
  const pathTo = useWorkspacePath();
  const { status } = entry;
  return (
    <article className={`integration-card integration-card--${status.kind}`}>
      <div className="integration-card__top">
        <IntegrationMark kind={entry.mark} size="lg" />
        <span className="integration-card__category">{categoryLabel(entry.category)}</span>
      </div>
      <h3 className="integration-card__name">{entry.name}</h3>
      <p className="integration-card__text">{entry.tagline}</p>
      <div className="integration-card__foot">
        {status.kind === "active" ? (
          <span className="integration-card__status integration-card__status--on">
            <span className="integration-card__dot" aria-hidden="true" />
            {status.lastUsedAt ? `${status.detail} · usada ${relativeTime(status.lastUsedAt)}` : status.detail}
          </span>
        ) : status.kind === "soon" ? (
          <span className="soon-badge">Próximamente</span>
        ) : (
          <span className="integration-card__status">Sin conectar</span>
        )}
        {entry.target && (
          <Link className="button button--secondary button--small" to={pathTo(TARGET_PATHS[entry.target])} aria-label={`${status.kind === "active" ? "Administrar" : "Configurar"} ${entry.name}`}>
            {status.kind === "active" ? "Administrar" : "Configurar"}
          </Link>
        )}
      </div>
    </article>
  );
}
