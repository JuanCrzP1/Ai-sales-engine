"""El Centro de ayuda: artículos en Markdown con un encabezado de metadatos, agrupados en temas que siguen el menú del panel.

Una sola fuente para tres lectores: las personas (el Centro de ayuda y la ayuda de cada pantalla del panel), los agentes de IA (las
herramientas `search_help` y `read_help_article` del servidor MCP) y, más adelante, la ayuda pública. Cada artículo es
`content/help/<tema>/<slug>.md`:

    ---
    title: Conecta tu WhatsApp con el código QR
    module: canales
    summary: Una frase que dice qué resuelve.
    order: 1
    updated: 2026-11-12
    keywords: qr, vincular, número
    related: numero-desconectado, buenas-practicas-whatsapp
    ---

Las reglas se revisan al cargar: un artículo mal escrito o un enlace a otro que no existe es un error, nunca una ayuda a medias.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date

from app.domain.business_config.errors import BusinessConfigError


@dataclass(frozen=True)
class HelpModule:
    id: str
    name: str
    description: str


# Los temas, en el orden del menú del panel: primero empezar, después atender y vender, y al final la configuración y la cuenta.
HELP_MODULES: tuple[HelpModule, ...] = (
    HelpModule("primeros-pasos", "Primeros pasos", "Crear tu cuenta y tu negocio, y dejar a tu asistente vendiendo"),
    HelpModule("conversaciones", "Conversaciones", "Atender en vivo, responder tú y pausar la IA"),
    HelpModule("respuestas-rapidas", "Respuestas rápidas", "Tus mensajes de siempre, a un «/» de distancia"),
    HelpModule("atencion-humana", "Atención humana", "Cuándo pasa un chat a tu equipo, el horario y los avisos"),
    HelpModule("clientes-y-ventas", "Clientes, ventas y reportes", "Las etapas de tus clientes, registrar ventas y ver resultados"),
    HelpModule("asistente", "Asistente IA", "Enseñarle lo que vendes, probarlo y publicarlo"),
    HelpModule("canales", "Canales", "Conectar tu WhatsApp y tu bot de Telegram, y mantenerlos conectados"),
    HelpModule("integraciones", "Integraciones y agentes", "La API del asistente, las claves y los agentes de IA"),
    HelpModule("inteligencia-artificial", "Inteligencia artificial", "Tu clave de OpenRouter, el modelo y lo que gastas"),
    HelpModule("cuenta", "Tu equipo y tu cuenta", "Invitar a tu equipo, los roles, tu perfil, la seguridad y eliminar"),
)
MODULE_IDS = frozenset(module.id for module in HELP_MODULES)

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_TITLE = 90
MAX_SUMMARY = 200
WORDS_PER_MINUTE = 200
SEARCH_LIMIT = 8
MAX_QUERY = 200

_FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.DOTALL)
_SECTION = re.compile(r"^## +(.+?)\s*$", re.MULTILINE)
# Un enlace a otro artículo: `[texto](slug)`. Los de pantallas del panel son `[texto](panel:ruta)` y los de afuera, `https://`.
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_ARTICLE_LINK = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PANEL_LINK = re.compile(r"^panel:[a-z0-9-]*(?:/[a-z0-9-]+)*$")
# Palabras que aparecen en casi todo y no dicen qué se busca.
_STOPWORDS = frozenset(
    "a al como con cual cuando de del el en es esta este hay la las le lo los mi mis o para pero por que se si sin su sus te tu tus un una uno y yo me".split()
)


class HelpArticleError(ValueError):
    """Un artículo mal escrito: se descubre al cargar la ayuda (y en las pruebas), nunca frente a quien la lee."""


class HelpArticleNotFoundError(BusinessConfigError):
    """El artículo no existe."""


@dataclass(frozen=True)
class HelpSection:
    id: str
    title: str


@dataclass(frozen=True)
class HelpArticle:
    slug: str
    module: str
    title: str
    summary: str
    order: int
    updated: date
    keywords: tuple[str, ...]
    related: tuple[str, ...]
    # Markdown, sin el encabezado de metadatos.
    body: str

    @property
    def minutes(self) -> int:
        return max(1, round(len(self.body.split()) / WORDS_PER_MINUTE))

    @property
    def sections(self) -> tuple[HelpSection, ...]:
        """Los títulos `##`, para el índice «En este artículo»."""
        return tuple(HelpSection(anchor_of(title), title) for title in _SECTION.findall(self.body))

    @property
    def links(self) -> tuple[str, ...]:
        """A dónde lleva cada enlace del texto (otro artículo, una pantalla del panel o una dirección de afuera)."""
        return tuple(target for _, target in _LINK.findall(self.body))


def normalize(text: str) -> str:
    """En minúsculas y sin tildes, para buscar «configuracion» y encontrar «Configuración»."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def anchor_of(title: str) -> str:
    """«Si algo falla» → «si-algo-falla»: el ancla de cada sección (la misma que calcula el panel)."""
    return re.sub(r"[^a-z0-9]+", "-", normalize(title)).strip("-")


def _list(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def parse_article(slug: str, source: str, *, module: str | None = None) -> HelpArticle:
    """El artículo de un archivo. `module` es la carpeta donde está: debe coincidir con el que declara."""
    where = f"«{slug}»"
    if not SLUG.match(slug):
        raise HelpArticleError(f"{where}: el nombre del archivo va en minúsculas, sin tildes y con guiones")
    match = _FRONTMATTER.match(source)
    if not match:
        raise HelpArticleError(f"{where}: le falta el encabezado de metadatos entre «---»")
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator or not key.strip():
            raise HelpArticleError(f"{where}: la línea «{line}» del encabezado no es «clave: valor»")
        value = value.strip()
        # Un valor con «:» puede ir entre comillas, como en YAML.
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1].strip()
        meta[key.strip()] = value
    unknown = sorted(set(meta) - {"title", "module", "summary", "order", "updated", "keywords", "related"})
    if unknown:
        raise HelpArticleError(f"{where}: no conozco {', '.join(unknown)} en el encabezado")
    title, summary, declared = meta.get("title", ""), meta.get("summary", ""), meta.get("module", "")
    if not title or len(title) > MAX_TITLE:
        raise HelpArticleError(f"{where}: el título es obligatorio y de máximo {MAX_TITLE} caracteres")
    if not summary or len(summary) > MAX_SUMMARY:
        raise HelpArticleError(f"{where}: el resumen es obligatorio y de máximo {MAX_SUMMARY} caracteres")
    if declared not in MODULE_IDS:
        raise HelpArticleError(f"{where}: el tema «{declared}» no existe; usa uno de {', '.join(sorted(MODULE_IDS))}")
    if module is not None and declared != module:
        raise HelpArticleError(f"{where}: está en la carpeta «{module}» pero dice que es del tema «{declared}»")
    try:
        order = int(meta.get("order", ""))
        updated = date.fromisoformat(meta.get("updated", ""))
    except ValueError as exc:
        raise HelpArticleError(f"{where}: «order» es un número y «updated» una fecha como 2026-11-12") from exc
    body = match.group(2).strip()
    if not body:
        raise HelpArticleError(f"{where}: el artículo no tiene texto")
    if body.startswith("# ") or "\n# " in body:
        raise HelpArticleError(f"{where}: el título va en el encabezado; dentro del texto, las secciones empiezan con «##»")
    for line in body.splitlines():
        # El panel muestra listas de un nivel: una sublista se vería pegada al texto.
        if re.match(r"^\s+([-*]|\d+\.)\s", line):
            raise HelpArticleError(f"{where}: no uses listas dentro de listas («{line.strip()[:40]}»)")
    article = HelpArticle(
        slug=slug,
        module=declared,
        title=title,
        summary=summary,
        order=order,
        updated=updated,
        keywords=_list(meta.get("keywords", "")),
        related=_list(meta.get("related", "")),
        body=body,
    )
    for target in article.links:
        if not (target.startswith("https://") or _ARTICLE_LINK.match(target) or _PANEL_LINK.match(target)):
            raise HelpArticleError(f"{where}: el enlace «{target}» no es otro artículo, una pantalla (panel:ruta) ni una dirección https")
    return article


def _plain(markdown: str) -> str:
    """El texto sin marcas, para buscar en él."""
    text = _LINK.sub(r"\1", markdown)
    return re.sub(r"[*`>#|]", " ", text)


def _terms(query: str) -> list[str]:
    words = re.findall(r"[a-z0-9ñ]+", normalize(query[:MAX_QUERY]))
    return [word for word in words if len(word) >= 2 and word not in _STOPWORDS]


def _stem(term: str) -> str:
    """La raíz de una palabra, para que «conectar» encuentre «conecta» y «conectado», y «pagos» encuentre «pago»."""
    return term if len(term) <= 4 else term[: max(4, len(term) - 2)]


class HelpLibrary:
    """Todos los artículos, revisados entre sí: nombres únicos y enlaces a artículos que existen."""

    def __init__(self, articles: Iterable[HelpArticle]) -> None:
        self._articles: dict[str, HelpArticle] = {}
        for article in articles:
            if article.slug in self._articles:
                raise HelpArticleError(f"«{article.slug}»: hay dos artículos con el mismo nombre")
            self._articles[article.slug] = article
        for article in self._articles.values():
            for slug in (*article.related, *(link for link in article.links if _ARTICLE_LINK.match(link))):
                if slug not in self._articles:
                    raise HelpArticleError(f"«{article.slug}»: enlaza a «{slug}», que no existe")
                if slug == article.slug:
                    raise HelpArticleError(f"«{article.slug}»: se enlaza a sí mismo")
        self._index = {
            slug: (normalize(article.title), normalize(" ".join((*article.keywords, article.summary))), normalize(_plain(article.body)))
            for slug, article in self._articles.items()
        }

    def __len__(self) -> int:
        return len(self._articles)

    def all(self) -> list[HelpArticle]:
        return sorted(self._articles.values(), key=lambda article: (MODULE_ORDER[article.module], article.order, article.title))

    def in_module(self, module: str) -> list[HelpArticle]:
        return [article for article in self.all() if article.module == module]

    def article(self, slug: str) -> HelpArticle:
        found = self._articles.get(slug)
        if found is None:
            raise HelpArticleNotFoundError("Ese artículo de ayuda no existe. Búscalo con search_help.")
        return found

    def related(self, article: HelpArticle) -> list[HelpArticle]:
        return [self._articles[slug] for slug in article.related]

    def search(self, query: str, limit: int = SEARCH_LIMIT) -> list[HelpArticle]:
        """Por palabras: el título pesa más que las palabras clave y el resumen, y estos más que el texto. Encuentra cada palabra
        aunque no esté igual («conectar» → «conecta»), sin tildes y sin las palabras que aparecen en todo («de», «la»)."""
        terms = _terms(query)
        if not terms:
            return []
        patterns = [re.compile(rf"\b{re.escape(_stem(term))}") for term in terms]
        scored: list[tuple[int, HelpArticle]] = []
        for slug, (title, keys, body) in self._index.items():
            score = 0
            matched = 0
            for pattern in patterns:
                hit = (6 if pattern.search(title) else 0) + (3 if pattern.search(keys) else 0) + (1 if pattern.search(body) else 0)
                score += hit
                matched += 1 if hit else 0
            if score:
                # Las que tienen TODAS las palabras buscadas van primero.
                scored.append((score + (10 if matched == len(patterns) else 0), self._articles[slug]))
        scored.sort(key=lambda item: (-item[0], MODULE_ORDER[item[1].module], item[1].order))
        return [article for _, article in scored[: max(1, limit)]]


MODULE_ORDER = {module.id: index for index, module in enumerate(HELP_MODULES)}


def module_named(module_id: str) -> HelpModule:
    return HELP_MODULES[MODULE_ORDER[module_id]]


def library_from_sources(sources: Sequence[tuple[str, str, str]]) -> HelpLibrary:
    """La ayuda armada de (tema, slug, texto) de cada archivo."""
    return HelpLibrary(parse_article(slug, text, module=module) for module, slug, text in sources)
