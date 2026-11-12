import { Link, useParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { formatUpdated } from "../../domain/help/help";
import { LoadingScreen } from "../../layout/StatusScreen";
import { HELP_ITEM, helpArticlePath, helpModulePath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useHelpArticle, useHelpIndex } from "../../state/useHelp";
import { Markdown } from "./Markdown";

/** Un artículo: dónde está (Ayuda › tema), su texto con el índice «En este artículo», los relacionados y lo demás de su tema. */
export function HelpArticlePage() {
  const { article: slug = "" } = useParams();
  const article = useHelpArticle(slug);
  const index = useHelpIndex();
  const pathTo = useWorkspacePath();

  if (article.status === "loading") return <LoadingScreen label="Cargando el artículo…" />;
  if (article.status === "error") {
    return (
      <div className="help-center">
        <nav className="help-crumbs" aria-label="Ruta">
          <Link to={pathTo(HELP_ITEM.path)}>Ayuda</Link>
        </nav>
        <Alert tone={article.missing ? "warning" : "danger"} title={article.missing ? "Este artículo no existe" : article.message}>
          {article.missing ? (
            <p>
              Quizá cambió de nombre. <Link to={pathTo(HELP_ITEM.path)}>Búscalo en el Centro de ayuda</Link>.
            </p>
          ) : (
            <Button variant="secondary" size="small" onClick={article.retry}>
              Reintentar
            </Button>
          )}
        </Alert>
      </div>
    );
  }

  const { value } = article;
  const siblings = index.status === "ready" ? (index.value.find((module) => module.id === value.module)?.articles ?? []) : [];
  const position = siblings.findIndex((item) => item.slug === value.slug);
  const previous = position > 0 ? siblings[position - 1] : undefined;
  const next = position >= 0 ? siblings[position + 1] : undefined;
  const more = siblings.filter((item) => item.slug !== value.slug && !value.related.some((related) => related.slug === item.slug));

  return (
    <div className="help-center help-article">
      <nav className="help-crumbs" aria-label="Ruta">
        <Link to={pathTo(HELP_ITEM.path)}>Ayuda</Link>
        <span aria-hidden="true">›</span>
        <Link to={pathTo(helpModulePath(value.module))}>{value.moduleName}</Link>
      </nav>

      <div className="help-article__layout">
        <article className="help-article__main" aria-labelledby="articulo-titulo">
          <header className="help-article__header">
            <h1 id="articulo-titulo" className="help-article__title">
              {value.title}
            </h1>
            <p className="help-article__summary">{value.summary}</p>
            <p className="help-article__meta">
              {value.minutes} min de lectura · Actualizado el {formatUpdated(value.updated)}
            </p>
          </header>
          <Markdown source={value.body} />

          {(previous || next) && (
            <nav className="help-article__pager" aria-label="Anterior y siguiente">
              {previous ? (
                <Link to={pathTo(helpArticlePath(previous.slug))} className="help-article__pager-link">
                  <small>Anterior</small>
                  <span>{previous.title}</span>
                </Link>
              ) : (
                <span />
              )}
              {next && (
                <Link to={pathTo(helpArticlePath(next.slug))} className="help-article__pager-link help-article__pager-link--next">
                  <small>Siguiente</small>
                  <span>{next.title}</span>
                </Link>
              )}
            </nav>
          )}
        </article>

        <aside className="help-article__aside">
          {value.sections.length > 1 && (
            <nav className="help-aside" aria-label="En este artículo">
              <p className="help-aside__title">En este artículo</p>
              <ul>
                {value.sections.map((section) => (
                  <li key={section.id}>
                    <a href={`#${section.id}`}>{section.title}</a>
                  </li>
                ))}
              </ul>
            </nav>
          )}
          {value.related.length > 0 && (
            <nav className="help-aside" aria-label="Relacionados">
              <p className="help-aside__title">Relacionados</p>
              <ul>
                {value.related.map((related) => (
                  <li key={related.slug}>
                    <Link to={pathTo(helpArticlePath(related.slug))}>{related.title}</Link>
                  </li>
                ))}
              </ul>
            </nav>
          )}
          {more.length > 0 && (
            <nav className="help-aside" aria-label={`Más de ${value.moduleName}`}>
              <p className="help-aside__title">Más de {value.moduleName}</p>
              <ul>
                {more.map((item) => (
                  <li key={item.slug}>
                    <Link to={pathTo(helpArticlePath(item.slug))}>{item.title}</Link>
                  </li>
                ))}
              </ul>
            </nav>
          )}
          <Link to={pathTo(HELP_ITEM.path)} className="help-aside__back">
            <Icon name="arrowLeft" size={14} /> Centro de ayuda
          </Link>
        </aside>
      </div>
    </div>
  );
}
