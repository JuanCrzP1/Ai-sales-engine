"""
Validación integral de los nueve negocios en el almacén de BusinessConfig, sobre una base SQLite temporal.

Se importan una vez y cada prueba trabaja con su propia copia de la base. La referencia es lo que leen hoy
de sus YAML, que estas pruebas solo leen. El motor no se conecta a este almacén: la comparación de prompts se
hace dentro de la prueba, apuntando el cargador actual a la base temporal.
"""
from __future__ import annotations

import copy
import functools
import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import func, select

from app.application.runtime import tenant_runtime_loader as loader
from app.application.runtime.tenant_runtime_loader import _load_legacy_sections
from app.domain.business_config.contract import SecretRef
from app.domain.business_config.errors import BusinessConfigError, SecretResolutionError
from app.domain.business_config.payment_data import SECRET_STORE_SOURCE, iter_payment_blocks, iter_secret_refs, payment_values
from app.infrastructure.business_config.database import DATABASE_URL_ENV, build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV, PaymentSecretStore
from app.infrastructure.business_config.runtime_access import dispose_shared_engines
from app.infrastructure.business_config.tables import business_config_secrets, business_configs, tenants
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_field_catalog import COMMERCIAL_CONTROLS, check_leaf, destination_path, find_entry, legacy_leaves, resolve_path
from app.infrastructure.config.legacy_store_migration import MIGRATION_AUTHOR, import_all
from pipeline_harness import TENANTS, reply, run_conversation

ROOT_DIR = Path(__file__).resolve().parents[1]
CONVERSATION = [
    ("Hola, necesito información", reply("Claro.")),
    ("¿Cuánto cuesta?", reply("Te cuento los precios.")),
    ("¿Y qué incluye? ¿Hacen envíos?", reply("Te explico lo que incluye.")),
    ("Quiero pagar por Nequi", reply("Listo.", "buy", payment_method="nequi")),
]


@functools.lru_cache(maxsize=None)
def _cached_sections(slug: str) -> str:
    return json.dumps(_load_legacy_sections(ConfigService(), slug), ensure_ascii=False)


def _sections(slug: str) -> dict:
    return json.loads(_cached_sections(slug))


def _yaml_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in sorted((ROOT_DIR / "project" / "config" / "tenants").glob("*/*.yaml")):
        digest.update(path.read_bytes())
    return digest.hexdigest()


@pytest.fixture(scope="module")
def key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture(scope="module")
def base_database(tmp_path_factory, key) -> Path:
    path = tmp_path_factory.mktemp("nueve_negocios") / "base.sqlite3"
    engine = create_business_config_engine(f"sqlite:///{path.as_posix()}")
    create_local_schema(engine)
    before = _yaml_fingerprint()
    report = import_all(build_business_config_service(engine, secrets_key=key), ConfigService())
    engine.dispose()
    assert report.created == sorted(TENANTS) and report.skipped == [] and report.unpublished == []
    assert _yaml_fingerprint() == before, "importar no modifica los YAML"
    return path


@pytest.fixture
def store(base_database, tmp_path, key):
    """Copia propia de la base ya importada: ninguna prueba afecta a otra."""
    path = tmp_path / "business_config.sqlite3"
    shutil.copy(base_database, path)
    engine = create_business_config_engine(f"sqlite:///{path.as_posix()}")
    yield SimpleNamespace(service=build_business_config_service(engine, secrets_key=key), engine=engine, path=path, secrets=PaymentSecretStore(engine, key))
    engine.dispose()


def _published_document(store, slug: str) -> dict:
    return store.service.get_published(slug).model_dump(mode="json", exclude_none=True)


def _with_settings(store, slug: str) -> dict:
    config = store.service.get_published(slug)
    return {
        **config.model_dump(mode="json", exclude_none=True),
        "engine_settings": config.engine_settings.model_dump(mode="json", exclude_none=True),
    }


# ---------------------------------------------------------------------------
# Importación
# ---------------------------------------------------------------------------

def test_the_nine_businesses_are_imported_and_published_once(store):
    summaries = store.service.list_businesses()
    assert [item.slug for item in summaries] == sorted(TENANTS)
    for item in summaries:
        assert (item.latest_version, item.published_version, item.draft_version) == (1, 1, None), item.slug
        assert item.name == _sections(item.slug)["business"]["name"]
        version = store.service.history(item.slug)[0]
        assert version.status == "published" and version.created_by == MIGRATION_AUTHOR and version.published_at.tzinfo is not None


def test_repeating_the_import_neither_duplicates_nor_overwrites(store):
    # Un negocio editado después de la importación no vuelve a su contenido original.
    document = _published_document(store, "saas")
    document["identity"]["description"] = "Descripción editada después de importar"
    version = store.service.save_changes("saas", document).version
    store.service.publish("saas", version)

    def _snapshot():
        with store.engine.connect() as conn:
            counts = (
                conn.execute(select(func.count()).select_from(tenants)).scalar(),
                conn.execute(select(func.count()).select_from(business_configs)).scalar(),
                conn.execute(select(func.count()).select_from(business_config_secrets)).scalar(),
            )
        return counts, [(s.slug, s.latest_version, s.published_version, s.draft_version) for s in store.service.list_businesses()]

    before = _snapshot()
    report = import_all(store.service, ConfigService())
    assert report.created == [] and report.skipped == sorted(TENANTS) and report.unpublished == []
    assert _snapshot() == before
    assert before[0][0] == len(TENANTS)
    assert store.service.get_published("saas").identity.description == "Descripción editada después de importar"


# ---------------------------------------------------------------------------
# Cada campo de los YAML, en su lugar dentro de la base
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("slug", TENANTS)
def test_every_yaml_field_is_stored_where_the_catalog_declares(store, slug):
    document = _with_settings(store, slug)
    resolve = store.secrets.resolver(slug)
    kinds = {"typed": 0, "technical": 0, "secret": 0, "policy": 0}
    problems = []
    for leaf in legacy_leaves(_sections(slug)):
        entry = find_entry(leaf.pattern)
        kinds[entry.kind] += 1
        if entry.kind == "secret":
            holder = resolve_path(document, destination_path(entry, leaf))
            if not str(leaf.value or "").strip():
                if holder is not None:
                    problems.append(f"{leaf.path}: dato vacío con referencia")
            elif holder is None or resolve(SecretRef(**holder)) != str(leaf.value):
                problems.append(f"{leaf.path}: el dato de pago guardado no coincide")
        elif problem := check_leaf(document, leaf):
            problems.append(problem)
    assert problems == []
    assert all(kinds.values()), kinds


@pytest.mark.parametrize("slug", TENANTS)
def test_identity_offer_and_prices(store, slug):
    sections, config = _sections(slug), store.service.get_published(slug)
    business, pricing = sections["business"], sections["pricing"]
    assert config.identity.name == business["name"] and config.identity.brand_name == business["brand_name"]
    assert config.identity.description == business["description"] and config.identity.industry == business["industry"]
    assert config.identity.value_proposition == business["promise"]
    assert config.identity.location.model_dump(mode="json", exclude_none=True) == business["location"]
    if "plans" in pricing:
        assert config.offer.model == "plans" and config.offer.catalog is None
        assert [plan.id for plan in config.offer.plans] == [plan["id"] for plan in pricing["plans"]]
        for plan, original in zip(config.offer.plans, pricing["plans"]):
            assert plan.name == original["name"]
            assert {price.currency: price.model_dump(exclude={"currency"}, exclude_none=True) for price in plan.prices} == original["pricing"]
            assert plan.includes == original.get("includes") and plan.not_included == original.get("not_included")
    else:
        catalog = pricing["catalog"]
        assert config.offer.model == "catalog" and not config.offer.plans
        assert [(c.id, c.name) for c in config.offer.catalog.categories] == [(c["id"], c["name"]) for c in catalog["categories"]]
        assert {i.id: {p.currency: p.amount for p in i.prices} for i in config.offer.catalog.items} == {i["id"]: i["price"] for i in catalog["items"]}
    assert config.terms.conditions == pricing.get("conditions")


@pytest.mark.parametrize("slug", TENANTS)
def test_messages_greeting_and_personality(store, slug):
    sections, config = _sections(slug), store.service.get_published(slug)
    settings, business = sections["config"], sections["business"]
    assert config.messages.welcome.enabled == settings["initial_message"]["enabled"]
    assert config.messages.welcome.text == settings["initial_message"]["text"]
    assert config.messages.payment_reported == settings["post_payment"]["on_user_report"]["message"]
    assert config.messages.payment_confirmed == settings["post_payment"]["on_payment_confirmed"]["message"]
    assert config.response_style.tone == business.get("tone") and config.response_style.voice == business.get("voice")
    assert config.response_style.length == settings["response"]["length"]
    assert config.response_style.max_words == settings["response"]["max_words"]


@pytest.mark.parametrize("slug", TENANTS)
def test_switches_and_commercial_options_keep_their_values(store, slug):
    document = _with_settings(store, slug)
    controls = {control.pattern for control in COMMERCIAL_CONTROLS}
    checked = 0
    for leaf in legacy_leaves(_sections(slug)):
        if leaf.pattern in controls:
            assert check_leaf(document, leaf) is None
            checked += 1
    assert checked >= 15, "cada negocio tiene interruptores y opciones comerciales"
    assert document["features"] == _sections(slug)["config"]["features"]


@pytest.mark.parametrize("slug", TENANTS)
def test_payment_methods_come_from_the_encrypted_store(store, slug):
    refs = [holder["secret_ref"] for holder in iter_secret_refs(_published_document(store, slug))]
    assert refs and all(ref.startswith(f"{SECRET_STORE_SOURCE}:") and "~" in ref for ref in refs)
    assert iter_payment_blocks(store.service.compile_sections(slug)["pricing"]) == iter_payment_blocks(_sections(slug)["pricing"])


# ---------------------------------------------------------------------------
# Compilación frente a la referencia original
# ---------------------------------------------------------------------------

def _differences(left, right, path: str = "") -> list[str]:
    if isinstance(left, dict) and isinstance(right, dict):
        return [item for key in sorted(set(left) | set(right)) for item in _differences(left.get(key, "<falta>"), right.get(key, "<falta>"), f"{path}.{key}" if path else key)]
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        return [item for index, (a, b) in enumerate(zip(left, right)) for item in _differences(a, b, f"{path}[{index}]")]
    return [] if left == right else [path]


@pytest.mark.parametrize("slug", TENANTS)
def test_compilation_has_no_differences_with_the_yaml(store, slug):
    compiled, reference = store.service.compile_sections(slug), _sections(slug)
    assert _differences(compiled, reference) == []
    assert compiled == reference


@pytest.mark.parametrize("slug", TENANTS)
def test_stored_configuration_gives_the_same_prompts_and_replies_as_the_yaml(store, key, monkeypatch, request, slug):
    """Solo dentro de esta prueba: el cargador actual, apuntado a la base temporal. El motor sigue con su fuente."""
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)
    from_yaml = run_conversation(slug, CONVERSATION, user_id="nueve_negocios")

    monkeypatch.setenv(SECRETS_KEY_ENV, key)
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    monkeypatch.setenv(loader.CONTRACT_STORE_ENV, "database")
    # Como en producción: el motor encuentra el almacén solo por su URL, sin sustituir ninguna pieza.
    monkeypatch.setenv(DATABASE_URL_ENV, f"sqlite:///{store.path.as_posix()}")
    request.addfinalizer(dispose_shared_engines)
    errors: list[dict] = []
    monkeypatch.setattr(loader.logger, "error", lambda event, extra=None: errors.append({"event": event, **(extra or {})}))
    assert run_conversation(slug, CONVERSATION, user_id="nueve_negocios") == from_yaml
    assert errors == [], "no debe usar el respaldo de los YAML"


# ---------------------------------------------------------------------------
# Lo que no viene de los YAML: promociones, instrucciones, políticas...
# ---------------------------------------------------------------------------

def _with_commercial_fields(document: dict) -> dict:
    document = copy.deepcopy(document)
    document["terms"]["promotions"] = [{"name": "Promoción de prueba", "details": "Dos por uno", "valid_until": "2999-12-31"}]
    document["terms"]["policies"] = {"warranty": "30 días", "returns": "Cambios en 5 días", "cancellation": "Hasta un día antes"}
    document["sales"]["instructions"] = ["Ofrece primero lo más vendido."]
    document["response_style"].update(formality="neutral", emojis=False, instructions=["Sin tecnicismos."])
    document["messages"].update(after_sale="Gracias", data_request="Tus datos", follow_up="¿Seguimos?", human_handoff="Te paso con alguien")
    document["knowledge"] = {"faqs": [{"question": "¿Atienden los domingos?", "answer": "Sí."}]}
    document["identity"]["opening_hours"] = [{"days": ["lunes", "martes"], "opens": "08:00", "closes": "18:00"}]
    for plan in document["offer"].get("plans") or []:
        plan["prices"][0]["annual"] = 1200
    catalog = document["offer"].get("catalog")
    if catalog:
        catalog["items"][0]["features"] = ["Característica de prueba"]
        currencies = {item["id"]: item["prices"][0]["currency"] for item in catalog["items"]}
        for entry in document["inventory"].get("items", []):
            for variant in entry.get("variants", []):
                variant["prices"] = [{"currency": currencies[entry["product_id"]], "amount": 10}]
    return document


@pytest.mark.parametrize("slug", TENANTS)
def test_commercial_fields_are_stored_published_and_recovered(store, slug):
    original = _published_document(store, slug)
    compiled_before = store.service.compile_sections(slug)
    enriched = _with_commercial_fields(original)

    version = store.service.save_changes(slug, enriched, created_by="prueba").version
    assert version == 2
    assert store.service.get_draft(slug).config.model_dump(mode="json", exclude_none=True) == enriched
    assert _published_document(store, slug) == original, "guardar no altera lo publicado"

    store.service.publish(slug, 2)
    assert _published_document(store, slug) == enriched
    assert store.service.compile_sections(slug) == compiled_before, "estos campos aún no llegan al motor"

    assert store.service.rollback(slug) == 1
    assert _published_document(store, slug) == original
    assert [(v.version, v.status) for v in store.service.history(slug)] == [(1, "published"), (2, "archived")]
    assert store.service.restore_version(slug, 2).version == 3
    assert store.service.get_draft(slug).config.model_dump(mode="json", exclude_none=True) == enriched


# ---------------------------------------------------------------------------
# Aislamiento y protección de pagos
# ---------------------------------------------------------------------------

def test_no_business_can_reach_the_data_of_another(store):
    published = {slug: _published_document(store, slug) for slug in TENANTS}
    refs = {slug: [h["secret_ref"] for h in iter_secret_refs(document)] for slug, document in published.items()}
    for owner in TENANTS:
        assert store.secrets.resolver(owner)(SecretRef(secret_ref=refs[owner][0]))
        for other in TENANTS:
            if other == owner:
                continue
            with pytest.raises(SecretResolutionError):
                store.secrets.resolver(other)(SecretRef(secret_ref=refs[owner][0]))
            with pytest.raises(BusinessConfigError):
                store.service.save_changes(other, published[owner])

    # Cambiar un negocio no altera a ningún otro.
    edited = copy.deepcopy(published["saas"])
    edited["identity"]["name"] = "Otro nombre"
    store.service.publish("saas", store.service.save_changes("saas", edited).version)
    for slug in TENANTS:
        if slug != "saas":
            assert _published_document(store, slug) == published[slug]
            assert len(store.service.history(slug)) == 1


def test_the_database_file_contains_no_payment_values(store):
    store.engine.dispose()
    raw = b"".join(path.read_bytes() for path in store.path.parent.glob(f"{store.path.name}*"))
    values = {value for slug in TENANTS for value in payment_values(_sections(slug))}
    assert values
    assert [value for value in values if value.encode("utf-8") in raw] == []
    assert b"legacy_yaml" not in raw, "la base no conserva referencias a los YAML"
