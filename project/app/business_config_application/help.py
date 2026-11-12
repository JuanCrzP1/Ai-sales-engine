"""El Centro de ayuda para el panel y para los agentes: los temas con sus artículos, buscar y leer uno. Es lo mismo para todos: no
toca datos de ningún negocio."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain.business_config.help import HELP_MODULES, MAX_QUERY, SEARCH_LIMIT, HelpArticle, HelpLibrary, library_from_sources, module_named

# Los artículos viajan con el motor: en Vercel solo se publica `project/`.
DEFAULT_HELP_DIR = Path(__file__).resolve().parents[2] / "content" / "help"


def article_summary(article: HelpArticle) -> dict[str, Any]:
    return {
        "slug": article.slug,
        "module": article.module,
        "title": article.title,
        "summary": article.summary,
        "minutes": article.minutes,
        "updated": article.updated.isoformat(),
    }


@dataclass(frozen=True)
class HelpService:
    library: HelpLibrary

    @classmethod
    def from_directory(cls, directory: Path = DEFAULT_HELP_DIR) -> HelpService:
        """Los artículos de `<tema>/<slug>.md`. Se leen una vez, al arrancar: uno mal escrito detiene el arranque con el motivo,
        igual que en las pruebas."""
        sources = [(path.parent.name, path.stem, path.read_text(encoding="utf-8")) for path in sorted(directory.glob("*/*.md"))]
        return cls(library_from_sources(sources))

    def index(self) -> dict[str, Any]:
        """Los temas en el orden del menú, cada uno con sus artículos en orden."""
        return {
            "modules": [
                {
                    "id": module.id,
                    "name": module.name,
                    "description": module.description,
                    "articles": [article_summary(article) for article in self.library.in_module(module.id)],
                }
                for module in HELP_MODULES
            ]
        }

    def search(self, query: str, limit: int = SEARCH_LIMIT) -> dict[str, Any]:
        query = query.strip()[:MAX_QUERY]
        return {"query": query, "results": [article_summary(article) for article in self.library.search(query, limit)]}

    def read(self, slug: str) -> dict[str, Any]:
        """El artículo completo: su texto en Markdown, sus secciones, su tema y los artículos relacionados."""
        article = self.library.article(slug)
        return {
            **article_summary(article),
            "module_name": module_named(article.module).name,
            "keywords": list(article.keywords),
            "body": article.body,
            "sections": [{"id": section.id, "title": section.title} for section in article.sections],
            "related": [article_summary(other) for other in self.library.related(article)],
        }
