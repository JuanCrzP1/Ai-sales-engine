import { Link, useSearchParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import type { HelpArticleSummary } from "../../domain/help/help";
import { LoadingScreen } from "../../layout/StatusScreen";
import { HELP_ITEM, helpArticlePath, helpModulePath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useHelpIndex, useHelpSearch } from "../../state/useHelp";
import { useCan } from "../../state/roleContext";
import { GettingStarted } from "./GettingStarted";

/**
 * Ayuda: el buscador primero, «Empieza aquí» con el avance del negocio y los temas en el orden del menú. Con `?q=` muestra lo que
 * encuentra; con `?tema=`, los artículos de ese tema.
 */
export function HelpCenterPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const topic = params.get("tema");
  const index = useHelpIndex();
  const results = useHelpSearch(query);
  const pathTo = useWorkspacePath();
  // «Empieza aquí» es de quien configura el negocio; un asesor va directo a los temas.
  const configures = useCan("configure");

  const setQuery = (value: string) => {
    const next = new URLSearchParams();
    if (value) next.set("q", value);
    setParams(next, { replace: true });
  };

  if (index.status === "loading") return <LoadingScreen label="Cargando la ayuda…" />;
  if (index.status === "error") {
    return (
      <Alert tone="danger" title={index.message}>
        <Button variant="secondary" size="small" onClick={index.retry}>
          Reintentar
        </Button>
      </Alert>
    );
  }
  const modules = index.value;
  const module = topic ? modules.find((item) => item.id === topic) : undefined;

  return (
    <div className="help-center">
      <header className="help-hero">
        {module ? (
          <nav className="help-crumbs" aria-label="Ruta">
            <Link to={pathTo(HELP_ITEM.path)}>Ayuda</Link>
          </nav>
        ) : (
          <p className="help-hero__eyebrow">Centro de ayuda</p>
        )}
        <h1 className="help-hero__title">{module ? module.name : "¿En qué te ayudamos?"}</h1>
        {module && <p className="help-hero__text">{module.description}</p>}
        <label className="help-search">
          <Icon name="search" size={18} />
          <input
            type="search"
            className="help-search__input"
            value={query}
            placeholder="Busca: conectar WhatsApp, pausar la IA, precios…"
            aria-label="Buscar en la ayuda"
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </header>

      {results ? (
        <section aria-label="Resultados de la búsqueda" className="help-results">
          {results.status === "loading" && <p className="help-results__note" role="status">Buscando…</p>}
          {results.status === "error" && <Alert tone="danger">{results.message}</Alert>}
          {results.status === "ready" && (
            <>
              <p className="help-results__note" role="status">
                {results.value.length === 0
                  ? `No encontramos nada con «${query.trim()}». Prueba con otras palabras, o revisa los temas.`
                  : `${results.value.length} ${results.value.length === 1 ? "artículo" : "artículos"} para «${query.trim()}»`}
              </p>
              <ArticleList articles={results.value} modules={modules.map(({ id, name }) => ({ id, name }))} />
            </>
          )}
        </section>
      ) : module ? (
        <ArticleList articles={module.articles} />
      ) : (
        <>
          {configures && <GettingStarted />}
          <section aria-labelledby="temas" className="help-topics">
            <h2 id="temas" className="section-heading">
              Temas
            </h2>
            <ul className="help-topics__grid">
              {modules.map((item) => (
                <li key={item.id}>
                  <Link to={pathTo(helpModulePath(item.id))} className="help-topic">
                    <span className="help-topic__name">{item.name}</span>
                    <span className="help-topic__text">{item.description}</span>
                    <span className="help-topic__count">
                      {item.articles.length} {item.articles.length === 1 ? "artículo" : "artículos"}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}

function ArticleList({ articles, modules }: { articles: HelpArticleSummary[]; modules?: { id: string; name: string }[] }) {
  const pathTo = useWorkspacePath();
  return (
    <ul className="help-list">
      {articles.map((article) => (
        <li key={article.slug}>
          <Link to={pathTo(helpArticlePath(article.slug))} className="help-list__item">
            <span className="help-list__icon" aria-hidden="true">
              <Icon name="file" size={18} />
            </span>
            <span className="help-list__text">
              <strong>{article.title}</strong>
              <span>{article.summary}</span>
              {modules && <small>{modules.find((module) => module.id === article.module)?.name}</small>}
            </span>
            <Icon name="arrowRight" size={16} />
          </Link>
        </li>
      ))}
    </ul>
  );
}
