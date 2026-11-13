"""Plantillas de negocio: empezar con un restaurante, una tienda, una agencia... en lugar de desde cero.

- Cada plantilla cumple el contrato y no trae nada propio de un negocio real (datos de pago, marca, dirección, zonas, pruebas de
  confianza o políticas): solo ejemplos para editar.
- Un negocio creado con una plantilla queda en borrador con su nombre y su identificador; nada se publica solo.
- El motor la entiende tal cual: su prompt ya trae los productos de ejemplo y el manual de su tipo de negocio.
"""
from __future__ import annotations

import copy
import json

import pytest

from app.application.runtime import runtime_from_sections
from app.business_config_application.templates import DEFAULT_TEMPLATES_DIR, BusinessTemplateCatalog
from app.domain.business_config.compiler import compile_business_config
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.payment_data import iter_secret_refs
from app.domain.business_config.templates import TemplateNotFoundError, template_from_dict
from app.infrastructure.ai.prompting import composer
from app.infrastructure.ai.prompting.sections.playbook import business_kind
from app.infrastructure.ai.prompting.view import PromptView
from test_admin_api import Local, _load

CATALOG = BusinessTemplateCatalog.from_directory()
TEMPLATE_IDS = [template.id for template in CATALOG.list()]
EXPECTED_KIND = {
    "restaurante": "catalog", "tienda": "catalog", "agencia_viajes": "booking", "escuela": "booking",
    "servicios_con_cita": "booking", "software": "plans",
}


def test_the_catalog_offers_the_templates_in_their_order():
    assert TEMPLATE_IDS == ["restaurante", "tienda", "agencia_viajes", "escuela", "servicios_con_cita", "software"]
    assert all(template.title and template.description and template.icon for template in CATALOG.list())


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_a_template_becomes_a_valid_business_with_its_name_and_nothing_private(template_id):
    document = CATALOG.get(template_id).instantiate("mi_negocio", "  Mi Negocio  ")
    config = BusinessConfig.model_validate(document)
    assert (config.tenant_slug, config.identity.name) == ("mi_negocio", "Mi Negocio")
    assert config.payments == [] and list(iter_secret_refs(document)) == []
    assert config.identity.brand_name is None and config.identity.credibility is None
    assert config.terms.policies is None and config.knowledge.faqs == []
    if config.identity.location is not None:
        assert config.identity.location.address is None and config.identity.location.city is None
        assert not (config.identity.location.coverage and config.identity.location.coverage.zones)
    # Instanciarla no cambia la plantilla: el siguiente negocio la recibe igual.
    assert CATALOG.get(template_id).document.get("tenant_slug") is None


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_the_engine_understands_a_template_as_it_comes(template_id):
    config = BusinessConfig.model_validate(CATALOG.get(template_id).instantiate("mi_negocio", "Mi Negocio"))
    runtime = runtime_from_sections("mi_negocio", compile_business_config(config, lambda ref: ""), channel="whatsapp")
    view = PromptView({**runtime, "tenant_slug": "mi_negocio", "conversation_state": "new"}, "¿Qué ofrecen?")
    prompt = composer.compose(view)
    assert "Nombre: Mi Negocio" in prompt
    offers = config.offer.plans or config.offer.catalog.items
    assert all(f"- {offer.name} — " in prompt for offer in offers)
    assert business_kind(view) == EXPECTED_KIND[template_id]
    assert "No hay medios de pago configurados" in prompt


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        pytest.param(lambda t: t["document"].update(payments=[{"id": "p", "transfer_enabled": False}]), "payments", id="datos_de_pago"),
        pytest.param(lambda t: t["document"]["identity"].update(brand_name="Marca real"), "brand_name", id="marca"),
        pytest.param(lambda t: t["document"]["identity"].update(credibility=["500 clientes felices"]), "credibility", id="testimonios"),
        pytest.param(lambda t: t["document"]["identity"]["location"].update(address="Calle 1"), "address", id="direccion"),
        pytest.param(lambda t: t["document"].update(tenant_slug="otro"), "tenant_slug", id="identificador"),
        pytest.param(lambda t: t.update(id="Con Espacios"), "identificador no válido", id="id_no_valido"),
    ],
)
def test_a_template_with_private_or_broken_data_is_rejected(change, problem):
    data = json.loads((DEFAULT_TEMPLATES_DIR / "restaurante.json").read_text(encoding="utf-8"))
    broken = copy.deepcopy(data)
    change(broken)
    with pytest.raises(ValueError, match=problem):
        template_from_dict(broken)


def test_an_unknown_template_is_reported():
    with pytest.raises(TemplateNotFoundError):
        CATALOG.get("no_existe")


def test_without_the_folder_only_starting_from_scratch_is_offered(tmp_path):
    assert BusinessTemplateCatalog.from_directory(tmp_path / "no_existe").list() == []


# ---------------------------------------------------------------------------
# API del panel
# ---------------------------------------------------------------------------

@pytest.fixture
def api(tmp_path):
    local = Local(tmp_path / "panel.sqlite3")
    yield local
    local.engine.dispose()


def test_the_panel_lists_the_templates_without_their_documents(api):
    response = api.client.get("/api/business-templates")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == TEMPLATE_IDS
    assert all(set(item) == {"id", "title", "description", "icon"} for item in response.json())


def test_a_business_created_from_a_template_starts_as_an_unpublished_draft(api):
    response = api.client.post("/api/businesses", json={"slug": "sabor_casero", "name": "Sabor Casero", "template": "restaurante"})
    assert response.status_code == 201
    assert response.json() | {"latest_version": 1} == {"slug": "sabor_casero", "name": "Sabor Casero", "latest_version": 1, "draft_version": 1, "published_version": None, "role": "owner"}
    stored = _load(api, "sabor_casero")
    expected = CATALOG.get("restaurante").instantiate("sabor_casero", "Sabor Casero")
    assert BusinessConfig.model_validate(stored["document"]) == BusinessConfig.model_validate(expected)


def test_a_business_from_scratch_still_starts_empty(api):
    response = api.client.post("/api/businesses", json={"slug": "desde_cero", "name": "Desde Cero"})
    assert response.status_code == 201 and response.json()["latest_version"] is None


def test_an_unknown_template_creates_nothing(api):
    response = api.client.post("/api/businesses", json={"slug": "fantasma", "name": "Fantasma", "template": "no_existe"})
    assert response.status_code == 422
    assert response.json()["issues"] == [{"path": "template", "message": "Elige otra plantilla."}]
    assert api.client.get("/api/businesses").json() == []
