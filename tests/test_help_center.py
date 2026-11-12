"""Centro de ayuda: los artículos de `project/content/help`, los mismos para el panel (Ayuda) y para los agentes (MCP).

- Los artículos reales cargan, cada tema tiene ayuda y los enlaces entre artículos existen.
- Un artículo mal escrito se descubre al cargar (y aquí), nunca frente a quien lo lee.
- La búsqueda encuentra sin tildes, con otra forma de la palabra y sin las palabras que aparecen en todo.
- La API pide sesión y devuelve los temas en el orden del menú, la búsqueda y el artículo completo; uno que no existe da 404.
"""
from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.business_config_application.help import HelpService
from app.business_config_application.mcp.tools.help import help_tools
from app.domain.business_config.access import Principal
from app.domain.business_config.help import (
    HELP_MODULES,
    HelpArticleError,
    HelpArticleNotFoundError,
    HelpLibrary,
    anchor_of,
    library_from_sources,
    parse_article,
)
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")


def _source(title="Conecta tu WhatsApp", module="canales", body="## Pasos\n\n1. Toca **Conectar**.\n", **extra) -> str:
    meta = {"title": title, "module": module, "summary": "Vincula tu número.", "order": "1", "updated": "2026-11-12", **extra}
    head = "\n".join(f"{key}: {value}" for key, value in meta.items())
    return f"---\n{head}\n---\n\n{body}"


@pytest.fixture(scope="module")
def real() -> HelpService:
    return HelpService.from_directory()


# ------------------------------------------------------------------------------------------------------------ los artículos reales


def test_the_real_articles_load_and_every_topic_has_help(real):
    assert len(real.library) >= 35
    modules = real.index()["modules"]
    assert [module["id"] for module in modules] == [module.id for module in HELP_MODULES]
    assert all(module["articles"] for module in modules), [module["id"] for module in modules if not module["articles"]]


def test_the_real_articles_are_tidy(real):
    articles = real.library.all()
    titles = [article.title for article in articles]
    assert len(titles) == len(set(titles)), "dos artículos con el mismo título confunden en la búsqueda"
    for article in articles:
        assert article.keywords, f"{article.slug}: sin palabras clave no se encuentra"
        assert article.updated <= date.today(), article.slug
        # Nada técnico ni a medias frente a quien administra el negocio.
        assert "TODO" not in article.body and "localhost" not in article.body, article.slug
    # «Empieza aquí» es la puerta de entrada: el panel la enlaza desde el inicio de la ayuda.
    assert real.library.article("empieza-aqui").module == "primeros-pasos"


def test_reading_an_article_brings_its_sections_and_related(real):
    article = real.read("conectar-whatsapp")
    assert article["module"] == "canales" and article["module_name"] == "Canales"
    assert article["body"].startswith("Tu asistente") and "---" not in article["body"][:3]
    assert {"id": "conectar", "title": "Conectar"} in article["sections"]
    assert [item["slug"] for item in article["related"]] == ["cuidar-tu-numero", "desconectar-whatsapp", "guardar-y-publicar"]
    assert article["minutes"] >= 1


@pytest.mark.parametrize(
    "query, first",
    [
        ("conectar whatsapp", "conectar-whatsapp"),
        ("conecto el whatsapp", "conectar-whatsapp"),
        ("CONFIGURACION y mi cuenta", "configuracion-y-mi-cuenta"),
        ("pausar la ia", "responder-y-pausar-la-ia"),
        ("borrar negocio", "eliminar-un-negocio"),
        ("clave openrouter", "clave-de-openrouter"),
        ("notificaciones iphone", "activar-notificaciones"),
    ],
)
def test_the_search_finds_what_a_person_would_write(real, query, first):
    assert real.search(query)["results"][0]["slug"] == first


def test_a_search_without_meaningful_words_finds_nothing(real):
    assert real.search("")["results"] == []
    assert real.search("de la el")["results"] == []
    assert len(real.search("asistente", limit=3)["results"]) == 3


# --------------------------------------------------------------------------------------------------------------- las reglas


def test_a_well_written_article_is_read_with_its_metadata():
    article = parse_article("conectar", _source(title='"Canales: conectar"', keywords="qr, vincular", related="otro"), module="canales")
    assert article.title == "Canales: conectar" and article.keywords == ("qr", "vincular") and article.related == ("otro",)
    assert article.updated == date(2026, 11, 12) and [section.title for section in article.sections] == ["Pasos"]


@pytest.mark.parametrize(
    "slug, source, folder, reason",
    [
        ("Conectar", _source(), "canales", "minúsculas"),
        ("conectar", "## Sin encabezado", "canales", "encabezado"),
        ("conectar", _source(module="ventas"), "ventas", "tema"),
        ("conectar", _source(), "cuenta", "carpeta"),
        ("conectar", _source(title=""), "canales", "título"),
        ("conectar", _source(order="primero"), "canales", "order"),
        ("conectar", _source(color="rojo"), "canales", "no conozco"),
        ("conectar", _source(body="# Título otra vez\n\nTexto"), "canales", "##"),
        ("conectar", _source(body="- Uno\n  - Dos"), "canales", "listas dentro de listas"),
        ("conectar", _source(body="Ve a [Canales](/negocios/x/canales)."), "canales", "enlace"),
        ("conectar", _source(body="Mira [esto](http://inseguro.com)."), "canales", "enlace"),
        ("conectar", _source(body=""), "canales", "texto"),
    ],
)
def test_a_badly_written_article_is_rejected_with_the_reason(slug, source, folder, reason):
    with pytest.raises(HelpArticleError, match=reason):
        parse_article(slug, source, module=folder)


def test_links_to_screens_other_articles_and_the_web_are_accepted():
    body = "Ve a [Canales](panel:canales), a [Ajustes](panel:configuracion/inteligencia-artificial), [otro](otro) y [OpenRouter](https://openrouter.ai)."
    assert parse_article("conectar", _source(body=body), module="canales").links == ("panel:canales", "panel:configuracion/inteligencia-artificial", "otro", "https://openrouter.ai")


def test_the_library_rejects_repeated_names_and_links_to_missing_articles():
    with pytest.raises(HelpArticleError, match="mismo nombre"):
        HelpLibrary([parse_article("a", _source()), parse_article("a", _source())])
    with pytest.raises(HelpArticleError, match="no existe"):
        library_from_sources([("canales", "a", _source(related="fantasma"))])
    with pytest.raises(HelpArticleError, match="no existe"):
        library_from_sources([("canales", "a", _source(body="Mira [esto](fantasma)."))])
    with pytest.raises(HelpArticleNotFoundError):
        library_from_sources([("canales", "a", _source())]).article("b")


def test_the_anchor_of_a_section_matches_the_panel():
    assert anchor_of("Si algo falla") == "si-algo-falla"
    assert anchor_of("¿Con qué versión responde?") == "con-que-version-responde"


# -------------------------------------------------------------------------------------------------------------------- la API


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return ANA if token == "token-de-ana" else None


@pytest.fixture
def client(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'ayuda.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    app = create_app(service, access=BusinessAccess(service, BusinessMembersStore(engine)), verifier=Tokens(), usage=UsageCounterStore(engine))
    yield TestClient(app)
    engine.dispose()


SESSION = {"Authorization": "Bearer token-de-ana"}


def test_the_help_needs_a_session(client):
    assert client.get("/api/help").status_code == 401
    assert client.get("/api/help/search", params={"q": "whatsapp"}).status_code == 401
    assert client.get("/api/help/articles/conectar-whatsapp").status_code == 401


def test_the_api_gives_the_topics_the_search_and_an_article(client):
    index = client.get("/api/help", headers=SESSION).json()
    assert index["modules"][0]["id"] == "primeros-pasos" and index["modules"][0]["articles"][0]["slug"] == "que-es-ai-sales-engine"
    found = client.get("/api/help/search", params={"q": "conectar whatsapp"}, headers=SESSION).json()
    assert found["query"] == "conectar whatsapp" and found["results"][0]["slug"] == "conectar-whatsapp"
    article = client.get("/api/help/articles/conectar-whatsapp", headers=SESSION).json()
    assert article["title"] == "Conecta tu WhatsApp con el código QR" and "panel:canales" in article["body"]


def test_an_unknown_article_is_a_404_in_spanish(client):
    response = client.get("/api/help/articles/no-existe", headers=SESSION)
    assert response.status_code == 404 and response.json()["message"] == "Ese artículo de ayuda no existe."
    assert client.get("/api/help/search", params={"q": "x" * 201}, headers=SESSION).status_code == 422


# ---------------------------------------------------------------------------------------------------------------------- MCP


def test_the_agent_tools_read_the_same_articles(real):
    search, read = help_tools(real)
    assert search.scope is None and read.scope is None and search.read_only and read.read_only
    assert search.run({"query": "pausar la ia"}, None)["results"][0]["slug"] == "responder-y-pausar-la-ia"
    assert read.run({"slug": "empieza-aqui"}, None)["body"] == real.library.article("empieza-aqui").body
    with pytest.raises(HelpArticleNotFoundError):
        read.run({"slug": "no-existe"}, None)
