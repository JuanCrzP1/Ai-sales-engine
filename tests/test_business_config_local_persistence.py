"""
Persistencia local de BusinessConfig v1, sobre un archivo SQLite real.

Comprueba los nueve negocios, la creación de negocios nuevos, el aislamiento, el guardado, la
recuperación de borradores, la publicación, el historial, la reversión y la protección de los datos de
pago. Nada de esto modifica los YAML ni el motor.
"""
from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import threading
import traceback
import uuid
from datetime import timezone
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import event, select, text
from sqlalchemy.exc import IntegrityError

from app.application.runtime import load_tenant_runtime_yaml
from app.application.runtime import tenant_runtime_loader as loader
from app.business_config_application import service as business_config_service
from app.business_config_application.ports import BusinessConfigStorage, PaymentSecretStorage
from app.domain.business_config.compiler import comparable_with_yaml, compile_business_config
from app.domain.business_config.contract import BusinessConfig, SecretRef
from app.domain.business_config.errors import (
    BusinessAlreadyExistsError,
    BusinessConfigError,
    BusinessNotFoundError,
    InvalidFieldsError,
    PaymentDataUnavailableError,
    SecretResolutionError,
    VersionConflictError,
    VersionNotFoundError,
)
from app.domain.business_config.diagnostics import review as diagnose
from app.domain.business_config.payment_data import iter_payment_fields, iter_secret_refs, mask_payment_value, payment_value_problem, payment_values
from app.infrastructure.business_config import database as business_config_database
from app.infrastructure.business_config import runtime_access
from app.infrastructure.business_config.database import (
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV, PaymentSecretStore
from app.infrastructure.business_config.repository import BusinessConfigRepository
from app.infrastructure.business_config.tables import business_config_secrets, business_configs, business_engine_settings, metadata, tenants
from app.infrastructure.config import legacy_store_migration
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_store_migration import import_all, import_prepared, prepare_tenant
from app.infrastructure.config.legacy_yaml_importer import import_legacy_sections
from pipeline_harness import TENANTS

ROOT_DIR = Path(__file__).resolve().parents[1]
EXAMPLE_PATH = ROOT_DIR / "project" / "config" / "contracts" / "v1" / "business-config.example.json"
LINK_REF = "secret_store:principal.link"
PHONE_REF = "secret_store:principal.transfer.0.number"


def _load_script():
    spec = importlib.util.spec_from_file_location("init_local_business_config", ROOT_DIR / "scripts" / "init_local_business_config.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _document(slug: str = "panaderia", **identity) -> dict:
    """Documento de un negocio nuevo, sin datos en claro: sus pagos solo son referencias."""
    document = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    document["tenant_slug"] = slug
    document["identity"].update(identity)
    document["payments"] = [
        {
            "id": "principal",
            "link": {"secret_ref": LINK_REF},
            "transfer_enabled": True,
            "transfer_methods": [{"type": "nequi", "number": {"secret_ref": PHONE_REF}}],
        }
    ]
    document["offer"]["catalog"]["payment_profile"] = "principal"
    return document


VALUES = {LINK_REF: "https://pagos.ejemplo/primero", PHONE_REF: "3005556677"}


def _with_length(document: dict, length: str) -> dict:
    return {**document, "response_style": {"length": length}}


def _payment_block(service, engine, slug: str, config=None) -> dict:
    config = config if config is not None else service.get_published(slug)
    compiled = compile_business_config(config, PaymentSecretStore(engine).resolver(slug))
    return compiled["pricing"]["catalog"]["payment"]


def _stored_document(service, slug: str) -> dict:
    return service.get_draft(slug).config.model_dump(mode="json", exclude_none=True)


@pytest.fixture
def database(tmp_path, monkeypatch):
    monkeypatch.setenv(SECRETS_KEY_ENV, Fernet.generate_key().decode())
    path = tmp_path / "local" / "business_config.sqlite3"
    engine = create_business_config_engine(f"sqlite:///{path.as_posix()}")
    create_local_schema(engine)
    yield engine, path
    engine.dispose()


@pytest.fixture
def service(database):
    return build_business_config_service(database[0])


@pytest.fixture
def engine(database):
    return database[0]


# ---------------------------------------------------------------------------
# Los nueve negocios
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("slug", TENANTS)
def test_each_business_is_stored_and_compiles_to_its_yaml(service, engine, slug):
    config_service = ConfigService()
    import_prepared(service, prepare_tenant(config_service, slug))

    summary = next(item for item in service.list_businesses() if item.slug == slug)
    assert (summary.latest_version, summary.published_version, summary.draft_version) == (1, 1, None)
    published = service.get_published(slug)
    refs = [holder["secret_ref"] for holder in iter_secret_refs(published.model_dump(mode="json"))]
    assert refs and all(ref.startswith("secret_store:") for ref in refs), "la base no debe depender de los YAML"
    sections = loader._load_legacy_sections(config_service, slug)
    assert comparable_with_yaml(compile_business_config(published, PaymentSecretStore(engine).resolver(slug))) == sections


def test_all_nine_businesses_coexist_without_payment_values_in_the_file(service, database):
    engine, path = database
    config_service = ConfigService()
    report = import_all(service, config_service)
    assert report.created == sorted(TENANTS) and report.skipped == []
    assert [item.slug for item in service.list_businesses()] == sorted(TENANTS)
    # Repetir no toca lo existente: no se crean versiones nuevas.
    again = import_all(service, config_service)
    assert again.created == [] and again.skipped == sorted(TENANTS)
    assert all(item.latest_version == 1 for item in service.list_businesses())

    engine.dispose()
    raw = path.read_bytes()
    values = {value for slug in TENANTS for value in payment_values(loader._load_legacy_sections(config_service, slug))}
    assert values, "los YAML de origen tienen datos de pago"
    assert [value for value in values if value.encode("utf-8") in raw] == []


@pytest.fixture
def engine_reads_this_store(database, monkeypatch):
    """El motor configurado como en producción: solo variables de entorno, sin sustituir ninguna pieza."""
    monkeypatch.setenv(business_config_database.DATABASE_URL_ENV, f"sqlite:///{database[1].as_posix()}")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "restaurant")
    monkeypatch.setenv(loader.CONTRACT_STORE_ENV, "database")
    yield
    runtime_access.dispose_shared_engines()


def test_runtime_reads_the_stored_business_without_changing_the_engine(service, engine_reads_this_store, monkeypatch):
    """El cargador del motor, con `BUSINESS_CONFIG_STORE=database`, lee el mismo archivo que escribe el panel: lo de los YAML,
    más el perfil comercial."""
    import_prepared(service, prepare_tenant(ConfigService(), "restaurant"))
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV)
    from_yaml = load_tenant_runtime_yaml("restaurant")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "restaurant")
    from_store = load_tenant_runtime_yaml("restaurant")
    assert from_store["config"]["profile"]["name"] == "Mesa Activa"
    assert comparable_with_yaml(from_store) == from_yaml


def test_what_the_panel_publishes_reaches_the_engine(service, engine_reads_this_store):
    """Publicar desde el panel cambia lo que recibe el motor; volver atrás lo devuelve."""
    import_prepared(service, prepare_tenant(ConfigService(), "restaurant"))
    before = load_tenant_runtime_yaml("restaurant")
    editable = service.get_editable("restaurant")
    document = editable.stored.config.model_dump(mode="json", exclude_none=True)
    document["messages"]["welcome"]["text"] = "Bienvenido a la versión publicada desde el panel"
    saved = service.save_changes("restaurant", document)
    service.publish("restaurant", saved.version)

    after = load_tenant_runtime_yaml("restaurant")
    assert after != before
    assert "Bienvenido a la versión publicada desde el panel" in json.dumps(after, ensure_ascii=False)
    service.rollback("restaurant")
    assert load_tenant_runtime_yaml("restaurant") == before


def test_the_engine_never_creates_the_store(tmp_path, monkeypatch):
    """Sin almacén, el motor sigue con sus YAML y no crea ningún archivo."""
    missing = tmp_path / "no-existe" / "business_config.sqlite3"
    monkeypatch.setenv(business_config_database.DATABASE_URL_ENV, f"sqlite:///{missing.as_posix()}")
    monkeypatch.setenv(loader.CONTRACT_STORE_ENV, "database")
    from_yaml = load_tenant_runtime_yaml("restaurant")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "restaurant")
    assert load_tenant_runtime_yaml("restaurant") == from_yaml
    assert not missing.parent.exists()


# ---------------------------------------------------------------------------
# Creación y listado
# ---------------------------------------------------------------------------

def test_new_business_can_be_created_saved_published_and_listed(service, engine):
    empty = service.create_business("floristeria", "Floristería")
    assert (empty.slug, empty.name, empty.latest_version) == ("floristeria", "Floristería", None)
    assert service.get_draft("floristeria") is None
    with pytest.raises(BusinessConfigError):
        service.get_published("floristeria")

    created = service.create_business("panaderia", "Panadería", document=_document(name="Pan y Café"), payment_values=VALUES)
    assert (created.name, created.latest_version, created.draft_version, created.published_version) == ("Pan y Café", 1, 1, None)
    assert [item.slug for item in service.list_businesses()] == ["floristeria", "panaderia"]

    service.publish("panaderia", 1)
    assert service.get_published("panaderia").identity.name == "Pan y Café"
    assert next(item for item in service.list_businesses() if item.slug == "panaderia").published_version == 1
    # El negocio nuevo no necesita YAML ni ajustes técnicos para compilar.
    assert _payment_block(service, engine, "panaderia")["link"] == VALUES[LINK_REF]


@pytest.mark.parametrize("slug, name", [("Con Mayusculas", "Nombre"), ("con-guion", "Nombre"), ("", "Nombre"), ("valido", "  ")])
def test_invalid_businesses_are_rejected(service, slug, name):
    with pytest.raises(BusinessConfigError):
        service.create_business(slug, name)
    assert service.list_businesses() == []


def test_duplicate_business_and_invalid_first_document_are_rejected(service):
    service.create_business("panaderia", "Panadería")
    with pytest.raises(BusinessAlreadyExistsError, match="ya existe"):
        service.create_business("panaderia", "Otra")
    with pytest.raises(BusinessConfigError):
        service.create_business("cafe", "Café", document=_document("otro_negocio"))
    with pytest.raises(BusinessConfigError):
        service.create_business("cafe", "Café", document={"tenant_slug": "cafe"})
    assert [item.slug for item in service.list_businesses()] == ["panaderia"]


# ---------------------------------------------------------------------------
# Guardado, borradores, publicación, historial y reversión
# ---------------------------------------------------------------------------

def test_save_and_recover_drafts(service):
    service.create_business("panaderia", "Panadería")
    first = service.save_changes("panaderia", _document(), payment_values=VALUES, created_by="dueño")
    assert (first.version, first.status) == (1, "draft")
    draft = service.get_draft("panaderia")
    assert draft.version.version == 1 and draft.version.created_by == "dueño" and draft.version.created_at is not None

    edited = _with_length(_stored_document(service, "panaderia"), "long")
    assert service.save_changes("panaderia", edited).version == 2
    assert service.get_draft("panaderia").config.response_style.length == "long"
    # Las versiones anteriores no cambian.
    assert service.get_version("panaderia", 1).config.response_style.length == "medium"
    # Un documento inválido no se guarda.
    with pytest.raises(BusinessConfigError):
        service.save_changes("panaderia", {**edited, "identity": {"name": "Sin datos"}})
    with pytest.raises(BusinessConfigError):
        service.get_version("panaderia", 99)
    assert len(service.history("panaderia")) == 2


def test_publish_history_rollback_and_recover_previous_versions(service):
    service.create_business("panaderia", "Panadería", document=_with_length(_document(), "short"), payment_values=VALUES)
    base = _stored_document(service, "panaderia")
    service.publish("panaderia", 1)
    assert service.get_draft("panaderia") is None, "publicar deja sin borrador en curso"

    assert service.save_changes("panaderia", _with_length(base, "long")).version == 2
    assert service.get_published("panaderia").response_style.length == "short", "un borrador no altera lo publicado"
    service.publish("panaderia", 2)
    assert service.get_published("panaderia").response_style.length == "long"
    assert [(v.version, v.status) for v in service.history("panaderia")] == [(1, "archived"), (2, "published")]
    assert all(v.published_at is not None for v in service.history("panaderia"))

    assert service.rollback("panaderia") == 1
    assert service.get_published("panaderia").response_style.length == "short"
    assert [(v.version, v.status) for v in service.history("panaderia")] == [(1, "published"), (2, "archived")]
    with pytest.raises(BusinessConfigError):
        service.rollback("panaderia")  # no hay una publicada anterior a la 1

    # Recuperar una versión crea un borrador nuevo y no publica nada.
    restored = service.restore_version("panaderia", 2, created_by="dueño")
    assert (restored.version, restored.status) == (3, "draft")
    assert service.get_draft("panaderia").config.response_style.length == "long"
    assert service.get_published("panaderia").response_style.length == "short"
    assert service.get_version("panaderia", 3).version.content_hash == service.get_version("panaderia", 2).version.content_hash


def test_old_draft_is_not_the_current_draft_after_publishing_a_newer_version(service):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    base = _stored_document(service, "panaderia")
    service.save_changes("panaderia", _with_length(base, "long"))
    service.publish("panaderia", 2)
    assert service.get_draft("panaderia") is None
    summary = service.list_businesses()[0]
    assert (summary.latest_version, summary.draft_version, summary.published_version) == (2, None, 2)


def test_data_survive_closing_and_reopening_the_database(database):
    engine, path = database
    service = build_business_config_service(engine)
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    service.publish("panaderia", 1)
    service.save_changes("panaderia", _with_length(_document(), "long"), payment_values=VALUES)
    engine.dispose()

    reopened = create_business_config_engine(f"sqlite:///{path.as_posix()}")
    create_local_schema(reopened)  # sobre una base existente no borra nada
    try:
        again = build_business_config_service(reopened)
        assert [item.slug for item in again.list_businesses()] == ["panaderia"]
        assert again.get_draft("panaderia").version.version == 2
        assert again.get_published("panaderia").identity.name == _document()["identity"]["name"]
        assert _payment_block(again, reopened, "panaderia")["link"] == VALUES[LINK_REF]
    finally:
        reopened.dispose()


# ---------------------------------------------------------------------------
# Aislamiento entre negocios
# ---------------------------------------------------------------------------

def test_businesses_are_isolated(service, engine):
    service.create_business("panaderia", "Panadería", document=_document("panaderia", name="Pan"), payment_values=VALUES)
    service.create_business("cafe", "Café", document=_document("cafe", name="Café"), payment_values={LINK_REF: "https://cafe.ejemplo/pago", PHONE_REF: "3110000000"})
    service.publish("panaderia", 1)

    # Los números de versión son por negocio y publicar uno no afecta al otro.
    assert [v.status for v in service.history("cafe")] == ["draft"]
    with pytest.raises(BusinessConfigError):
        service.get_published("cafe")
    service.publish("cafe", 1)
    assert service.get_published("cafe").identity.name == "Café"
    assert service.get_published("panaderia").identity.name == "Pan"

    # Un negocio no puede guardar el documento de otro.
    with pytest.raises(BusinessConfigError):
        service.save_changes("cafe", _document("panaderia"))
    assert len(service.history("cafe")) == 1

    # Los datos de pago del otro negocio no se pueden leer, aunque se conozca su referencia.
    pan_ref = next(iter_secret_refs(service.get_published("panaderia").model_dump(mode="json")))["secret_ref"]
    assert PaymentSecretStore(engine).resolver("panaderia")(SecretRef(secret_ref=pan_ref)) == VALUES[LINK_REF]
    with pytest.raises(SecretResolutionError):
        PaymentSecretStore(engine).resolver("cafe")(SecretRef(secret_ref=pan_ref))
    # Y un documento que apunte a ellos no se puede publicar.
    stolen = _document("cafe")
    stolen["payments"][0]["link"]["secret_ref"] = pan_ref
    version = service.save_changes("cafe", stolen, payment_values={PHONE_REF: "3110000000"}).version
    with pytest.raises(SecretResolutionError):
        service.publish("cafe", version)
    assert service.get_published("cafe").model_dump(mode="json") == service.get_version("cafe", 1).config.model_dump(mode="json")


def test_a_tampered_row_of_another_business_is_not_served(service, engine):
    service.create_business("panaderia", "Panadería", document=_document("panaderia"), payment_values=VALUES)
    service.create_business("cafe", "Café", document=_document("cafe"), payment_values=VALUES)
    with engine.begin() as conn:
        conn.execute(text("UPDATE business_configs SET document = (SELECT document FROM business_configs b JOIN tenants t ON b.tenant_id = t.id WHERE t.slug = 'cafe')"))
    with pytest.raises(BusinessConfigError):
        service.get_version("panaderia", 1)


def test_foreign_keys_are_enforced_in_sqlite(engine):
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("INSERT INTO business_engine_settings (tenant_id, document, updated_at) VALUES ('00000000000000000000000000000000', '{}', CURRENT_TIMESTAMP)"))


def test_version_numbers_belong_to_each_business(service):
    service.create_business("panaderia", "Panadería", document=_document("panaderia"), payment_values=VALUES)
    service.create_business("cafe", "Café", document=_document("cafe"), payment_values=VALUES)
    base = _stored_document(service, "panaderia")
    service.save_changes("panaderia", base)
    service.save_changes("panaderia", base)
    assert [item.version for item in service.history("panaderia")] == [1, 2, 3]
    assert [item.version for item in service.history("cafe")] == [1]
    assert service.save_changes("cafe", _stored_document(service, "cafe")).version == 2


def test_a_version_of_another_business_cannot_be_read_published_or_restored(service):
    service.create_business("panaderia", "Panadería", document=_document("panaderia"), payment_values=VALUES)
    service.create_business("cafe", "Café", document=_document("cafe"), payment_values=VALUES)
    service.save_changes("cafe", _stored_document(service, "cafe"))
    other_before = service.history("cafe")
    for action in (service.get_version, service.publish, service.restore_version):
        with pytest.raises(VersionNotFoundError):
            action("panaderia", 2)  # solo existe en el otro negocio
    assert [item.version for item in service.history("panaderia")] == [1]
    assert service.history("cafe") == other_before


def test_publishing_rolling_back_and_restoring_do_not_touch_another_business(service, engine):
    def _state(slug):
        with engine.connect() as conn:
            tenant_id = conn.execute(select(tenants.c.id).where(tenants.c.slug == slug)).scalar_one()
            secrets = conn.execute(select(business_config_secrets).where(business_config_secrets.c.tenant_id == tenant_id)).all()
        return service.history(slug), service.get_published(slug).model_dump(mode="json"), secrets

    for slug in ("panaderia", "cafe"):
        service.create_business(slug, slug, document=_document(slug), payment_values=VALUES)
        service.publish(slug, 1)
        service.publish(slug, service.save_changes(slug, _with_length(_document(slug), "long"), payment_values=VALUES).version)
    other_before = _state("cafe")

    assert service.rollback("panaderia") == 1
    restored = service.restore_version("panaderia", 2)
    service.publish("panaderia", restored.version)
    assert service.save_changes("panaderia", _document("panaderia"), payment_values=VALUES).version == 4

    assert _state("cafe") == other_before


def test_each_imported_business_keeps_its_own_documents_and_payment_data(service, engine):
    import_all(service, ConfigService())
    with engine.connect() as conn:
        owners = {row.id: row.slug for row in conn.execute(select(tenants)).all()}
        documents = conn.execute(select(business_configs.c.tenant_id, business_configs.c.document)).all()
        secrets = conn.execute(select(business_config_secrets.c.tenant_id, business_config_secrets.c.ref_key)).all()
    assert len(owners) == len(TENANTS)
    assert all(row.document["tenant_slug"] == owners[row.tenant_id] for row in documents)
    for slug in TENANTS:
        refs = {holder["secret_ref"] for holder in iter_secret_refs(service.get_published(slug).model_dump(mode="json"))}
        assert refs == {f"secret_store:{row.ref_key}" for row in secrets if owners[row.tenant_id] == slug}, slug


def test_a_version_without_its_business_is_refused_by_the_database(engine):
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(business_configs.insert().values(tenant_id=uuid.uuid4(), version=1, schema_version="1.0", status="draft", document={}, content_hash="x"))


def test_the_database_allows_one_published_version_per_business(service, engine):
    for slug in ("panaderia", "cafe"):
        service.create_business(slug, slug, document=_document(slug), payment_values=VALUES)
        service.publish(slug, 1)  # cada negocio tiene la suya, sin estorbarse
    service.save_changes("panaderia", _document("panaderia"), payment_values=VALUES)
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(business_configs.update().where(business_configs.c.version == 2).values(status="published"))


def test_deleting_a_business_leaves_nothing_behind(service, engine):
    for slug in ("panaderia", "cafe"):
        service.create_business(slug, slug, document=_document(slug), payment_values=VALUES)
        service.save_engine_settings(slug, {"schema_version": "1.0", "tenant_slug": slug})
    service.delete_business("panaderia")
    with engine.connect() as conn:
        remaining = set(conn.execute(select(tenants.c.id)).scalars())
        assert len(remaining) == 1
        for table in (business_configs, business_config_secrets, business_engine_settings):
            assert set(conn.execute(select(table.c.tenant_id)).scalars()) == remaining, table.name
    with pytest.raises(BusinessNotFoundError):
        service.history("panaderia")


# ---------------------------------------------------------------------------
# Guardado: la versión y sus datos de pago van juntos, y no se pisan cambios
# ---------------------------------------------------------------------------

def test_a_failure_writing_payment_data_saves_nothing(service, engine, monkeypatch):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    original = PaymentSecretStore.write

    def _fail_halfway(store, conn, tenant_id, secrets):
        original(store, conn, tenant_id, dict(list(secrets.items())[:1]))
        raise RuntimeError("fallo a mitad de la escritura")

    monkeypatch.setattr(PaymentSecretStore, "write", _fail_halfway)
    with pytest.raises(RuntimeError):
        service.save_changes("panaderia", _document(), payment_values={LINK_REF: "https://pagos.ejemplo/segundo", PHONE_REF: "3000000002"})
    assert len(service.history("panaderia")) == 1
    with engine.connect() as conn:
        assert len(conn.execute(select(business_config_secrets)).all()) == 2, "no quedan datos de pago huérfanos"


def test_a_version_the_database_refuses_leaves_no_payment_data(service, engine):
    service.create_business("panaderia", "Panadería")
    with engine.begin() as conn:
        conn.execute(text("CREATE TRIGGER rechaza_versiones BEFORE INSERT ON business_configs BEGIN SELECT RAISE(ABORT, 'rechazada'); END"))
    with pytest.raises(BusinessConfigError):
        service.save_changes("panaderia", _document(), payment_values=VALUES)
    with engine.connect() as conn:
        assert conn.execute(select(business_config_secrets)).all() == []


def test_saving_from_an_outdated_version_is_rejected(service):
    service.create_business("panaderia", "Panadería")
    assert service.save_changes("panaderia", _document(), payment_values=VALUES, expected_version=None).version == 1
    base = _stored_document(service, "panaderia")
    assert service.save_changes("panaderia", base, expected_version=1).version == 2
    for outdated in (1, None, 99):
        with pytest.raises(VersionConflictError):
            service.save_changes("panaderia", base, expected_version=outdated)
    assert len(service.history("panaderia")) == 2


def test_the_storage_detects_an_outdated_version_inside_its_transaction(service, engine):
    """Aunque otro guardado llegue después de la comprobación previa del servicio."""
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    base = _stored_document(service, "panaderia")
    service.save_changes("panaderia", base)
    with pytest.raises(VersionConflictError):
        BusinessConfigRepository(engine, PaymentSecretStore(engine)).save_draft("panaderia", base, expected_version=1, payment_secrets={"secret_store:nuevo": "valor"})
    assert len(service.history("panaderia")) == 2
    with engine.connect() as conn:
        assert len(conn.execute(select(business_config_secrets)).all()) == 2, "el dato de un guardado rechazado no se escribe"


def test_only_one_of_several_saves_from_the_same_version_wins(service):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    base = _stored_document(service, "panaderia")
    barrier = threading.Barrier(6)
    results: list[str] = []

    def _save() -> None:
        barrier.wait()
        try:
            service.save_changes("panaderia", base, expected_version=1)
            results.append("guardado")
        except VersionConflictError:
            results.append("conflicto")

    threads = [threading.Thread(target=_save) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(results) == ["conflicto"] * 5 + ["guardado"]
    assert [item.version for item in service.history("panaderia")] == [1, 2]


def test_a_rollback_that_cannot_be_completed_changes_nothing(service, engine):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    service.publish("panaderia", 1)
    first_refs = [holder["secret_ref"] for holder in iter_secret_refs(service.get_published("panaderia").model_dump(mode="json"))]
    service.publish("panaderia", service.save_changes("panaderia", _document(), payment_values={LINK_REF: "https://pagos.ejemplo/segundo", PHONE_REF: "3000000002"}).version)
    with engine.begin() as conn:
        conn.execute(business_config_secrets.delete().where(business_config_secrets.c.ref_key.in_([ref.removeprefix("secret_store:") for ref in first_refs])))

    with pytest.raises(PaymentDataUnavailableError):
        service.rollback("panaderia")

    assert [(v.version, v.status) for v in service.history("panaderia")] == [(1, "archived"), (2, "published")]
    assert _payment_block(service, engine, "panaderia")["link"] == "https://pagos.ejemplo/segundo"


# ---------------------------------------------------------------------------
# Consultas por negocio
# ---------------------------------------------------------------------------

def test_the_summary_of_a_business_is_the_same_as_in_the_listing(service):
    service.create_business("sin_versiones", "Sin versiones")
    service.create_business("borrador", "Borrador", document=_document("borrador", name="Nombre del borrador"), payment_values=VALUES)
    service.create_business("publicado", "Publicado", document=_document("publicado"), payment_values=VALUES)
    service.publish("publicado", 1)
    service.save_changes("publicado", _with_length(_document("publicado"), "long"), payment_values=VALUES)
    listing = service.list_businesses()
    assert len(listing) == 3
    for summary in listing:
        assert service.get_business(summary.slug) == summary
    with pytest.raises(BusinessNotFoundError):
        service.get_business("no_existe")


def test_listing_does_not_query_each_business_separately(service, engine):
    def _statements() -> int:
        seen: list[str] = []

        def _record(_conn, _cursor, statement, *_rest) -> None:
            seen.append(statement)

        event.listen(engine, "before_cursor_execute", _record)
        try:
            service.list_businesses()
        finally:
            event.remove(engine, "before_cursor_execute", _record)
        return len(seen)

    service.create_business("panaderia", "Panadería", document=_document("panaderia"), payment_values=VALUES)
    with_one = _statements()
    for slug in ("cafe", "floristeria", "tienda"):
        service.create_business(slug, slug, document=_document(slug), payment_values=VALUES)
    assert _statements() == with_one


# ---------------------------------------------------------------------------
# Protección de los datos de pago
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("kind", "value", "valid"),
    [
        ("link", "https://pagos.ejemplo/abc", True),
        ("link", "http://pagos.ejemplo", True),
        ("link", "  https://pagos.ejemplo  ", True),
        ("link", "pagos.ejemplo/abc", False),
        ("link", "https://", False),
        ("link", "ftp://pagos.ejemplo", False),
        ("link", "https://con espacio.ejemplo", False),
        ("mobile", "3001234567", True),
        ("mobile", "300 123 4567", True),
        ("mobile", "2001234567", False),
        ("mobile", "300123456", False),
        ("mobile", "30012345678", False),
        ("mobile", "٣٠٠١٢٣٤٥٦٧", False),
        ("account", "123456", True),
        ("account", "123-456 789", True),
        ("account", "12345", False),
        ("account", "abc123456", False),
        ("account", "1" * 21, False),
        ("reference", "mi-llave", True),
        ("reference", "   ", False),
    ],
)
def test_payment_value_formats(kind, value, valid):
    assert (payment_value_problem(kind, value) is None) is valid


def test_payment_fields_are_found_with_their_path_and_kind():
    document = _document()
    document["payments"][0]["transfer_methods"] = [
        {"type": "nequi", "number": {"secret_ref": "secret_store:a"}},
        {"type": "bank", "bank": "Banco", "account_type": "ahorros", "account_number": {"secret_ref": "secret_store:b"}},
        {"type": "breb", "reference": {"secret_ref": "secret_store:c"}},
    ]
    assert [(item.path, item.kind, item.ref) for item in iter_payment_fields(document)] == [
        ("payments.0.link", "link", LINK_REF),
        ("payments.0.transfer_methods.0.number", "mobile", "secret_store:a"),
        ("payments.0.transfer_methods.1.account_number", "account", "secret_store:b"),
        ("payments.0.transfer_methods.2.reference", "reference", "secret_store:c"),
    ]


def test_payment_values_with_a_wrong_format_are_not_saved_and_are_not_repeated(service, engine):
    service.create_business("panaderia", "Panadería")
    malformed = {LINK_REF: "MARCA-SIN-FORMATO", PHONE_REF: "12345"}
    with pytest.raises(InvalidFieldsError) as error:
        service.save_changes("panaderia", _document(), payment_values=malformed)
    assert [issue.path for issue in error.value.issues] == ["payments.0.link", "payments.0.transfer_methods.0.number"]
    assert "MARCA-SIN-FORMATO" not in "".join(traceback.format_exception(error.value))
    assert service.history("panaderia") == []
    with engine.connect() as conn:
        assert conn.execute(select(business_config_secrets)).all() == []


@pytest.mark.parametrize(
    ("kind", "value", "masked"),
    [
        ("link", "https://pagos.ejemplo/codigo-del-negocio?orden=1#fin", "https://pagos.ejemplo/••••"),
        ("link", "https://usuario:clave@pagos.ejemplo:8443/codigo", "https://pagos.ejemplo/••••"),
        ("link", "https://pagos.ejemplo", "https://••••.ejemplo"),
        ("link", "https://pagos.ejemplo/", "https://••••.ejemplo"),
        ("link", "https://localhost", "••••"),
        ("link", "no es un enlace", "••••"),
        ("link", "https://[no-es-ipv6/abc", "••••"),
        ("mobile", "3001234567", "••••4567"),
        ("mobile", "300 123 4567", "••••4567"),
        ("account", "123-456 7890", "••••7890"),
        ("account", "1234567", "••••567"),
        ("account", "123456", "••••56"),
        ("reference", "mi-llave-privada", "••••ada"),
        ("reference", "abcdef", "••••ef"),
        ("reference", "abcde", "••••"),
        ("reference", "abc", "••••"),
    ],
)
def test_masks_show_only_enough_to_recognize_the_value(kind, value, masked):
    assert mask_payment_value(kind, value) == masked
    assert value not in masked


def test_a_mask_never_reveals_half_of_the_value_nor_its_length():
    for length in range(6, 40):
        value = "7" * length
        visible = mask_payment_value("account", value).removeprefix("••••")
        assert len(visible) < length / 2
        assert len(mask_payment_value("account", value)) <= 8


def test_inactive_methods_and_links_are_not_compiled_nor_need_their_data():
    document = _document()
    document["payments"][0]["transfer_methods"].append({"type": "daviplata", "number": {"secret_ref": "secret_store:otra"}})

    def _compile(change) -> dict:
        edited = copy.deepcopy(document)
        change(edited["payments"][0])
        values = {LINK_REF: VALUES[LINK_REF], PHONE_REF: VALUES[PHONE_REF], "secret_store:otra": "3110000000"}
        requested: list[str] = []

        def _resolve(ref: SecretRef) -> str:
            requested.append(ref.secret_ref)
            return values[ref.secret_ref]

        block = compile_business_config(BusinessConfig.model_validate(edited), _resolve)["pricing"]["catalog"]["payment"]
        return {"block": block, "requested": requested}

    # Sin indicar nada, o activos de forma explícita, compilan igual.
    both = _compile(lambda profile: None)
    assert both["block"]["link"] == VALUES[LINK_REF]
    assert [method["type"] for method in both["block"]["transfer"]["methods"]] == ["nequi", "daviplata"]
    assert _compile(lambda profile: (profile.update(link_enabled=True), profile["transfer_methods"][0].update(enabled=True)))["block"] == both["block"]

    # Una cuenta inactiva no se ofrece ni se lee.
    paused = _compile(lambda profile: profile["transfer_methods"][0].update(enabled=False))
    assert [method["type"] for method in paused["block"]["transfer"]["methods"]] == ["daviplata"]
    assert paused["block"]["transfer"]["enabled"] is True
    assert PHONE_REF not in paused["requested"]

    # Un enlace inactivo tampoco.
    no_link = _compile(lambda profile: profile.update(link_enabled=False))
    assert no_link["block"]["link"] == ""
    assert LINK_REF not in no_link["requested"]

    # Con todas las cuentas inactivas, las transferencias quedan apagadas.
    none = _compile(lambda profile: [method.update(enabled=False) for method in profile["transfer_methods"]])
    assert none["block"]["transfer"] == {"enabled": False, "methods": []}

    # La etiqueta sirve para reconocer la cuenta en el panel: no llega al motor.
    labelled = _compile(lambda profile: profile["transfer_methods"][0].update(label="Cuenta de la tienda"))
    assert labelled["block"] == both["block"]


def test_optional_payment_fields_do_not_appear_unless_they_are_used():
    stored = BusinessConfig.model_validate(_document()).model_dump(mode="json", exclude_none=True)
    profile = stored["payments"][0]
    assert "link_enabled" not in profile
    assert {"label", "enabled"}.isdisjoint(profile["transfer_methods"][0])


def test_diagnostics_consider_only_the_active_link(service):
    document = _document()
    document["capabilities"]["closing_methods"]["payment_link"] = True
    assert "cierre_por_link_sin_link" not in {item.code for item in diagnose(BusinessConfig.model_validate(document))}
    document["payments"][0]["link_enabled"] = False
    found = [item for item in diagnose(BusinessConfig.model_validate(document)) if item.code == "cierre_por_link_sin_link"]
    assert [item.message for item in found] == ["El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene un link activo."]


def test_payment_values_are_encrypted_and_only_references_are_stored(service, database):
    engine, path = database
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    service.publish("panaderia", 1)
    with engine.connect() as conn:
        document = json.dumps(conn.execute(select(business_configs.c.document)).scalar_one())
        ciphertexts = conn.execute(select(business_config_secrets.c.ciphertext)).scalars().all()
    assert len(ciphertexts) == 2
    for value in VALUES.values():
        assert value not in document and all(value not in ciphertext for ciphertext in ciphertexts)
    engine.dispose()
    raw = path.read_bytes()
    assert all(value.encode("utf-8") not in raw for value in VALUES.values())


def test_editing_payment_data_does_not_touch_what_is_published_and_rollback_restores_it(service, engine):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    service.publish("panaderia", 1)
    stored = _document()
    assert _payment_block(service, engine, "panaderia")["link"] == VALUES[LINK_REF]

    version = service.save_changes("panaderia", stored, payment_values={LINK_REF: "https://pagos.ejemplo/segundo", PHONE_REF: "3000000002"}).version
    assert _payment_block(service, engine, "panaderia")["link"] == VALUES[LINK_REF], "el borrador no altera lo publicado"
    draft = service.get_draft("panaderia").config
    assert _payment_block(service, engine, "panaderia", draft)["link"] == "https://pagos.ejemplo/segundo"

    service.publish("panaderia", version)
    assert _payment_block(service, engine, "panaderia")["link"] == "https://pagos.ejemplo/segundo"
    service.rollback("panaderia")
    assert _payment_block(service, engine, "panaderia")["link"] == VALUES[LINK_REF], "revertir devuelve los datos de pago de esa versión"
    assert _payment_block(service, engine, "panaderia")["transfer"]["methods"][0]["number"] == VALUES[PHONE_REF]


def test_saving_without_new_values_keeps_the_current_payment_data(service, engine):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    version = service.save_changes("panaderia", _with_length(_stored_document(service, "panaderia"), "long")).version
    service.publish("panaderia", version)
    assert _payment_block(service, engine, "panaderia")["link"] == VALUES[LINK_REF]


def test_publishing_with_missing_payment_data_changes_nothing(service):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    service.publish("panaderia", 1)
    version = service.save_changes("panaderia", _with_length(_document(), "long")).version  # referencias sin valor
    with pytest.raises(SecretResolutionError):
        service.publish("panaderia", version)
    assert service.get_published("panaderia").response_style.length == "medium"
    assert [(v.version, v.status) for v in service.history("panaderia")] == [(1, "published"), (2, "draft")]


@pytest.mark.parametrize(
    "mutate, values",
    [
        (lambda d: d["payments"][0].update(link="https://pagos.ejemplo/en-claro"), {PHONE_REF: VALUES[PHONE_REF]}),  # valor en claro en un campo de pago
        (lambda d: d["sales"].update(instructions=["Paga en https://pagos.ejemplo/primero"]), VALUES),  # valor en un texto libre
        (lambda d: None, {**VALUES, "secret_store:otro": "valor-sin-referencia"}),  # dato sin referencia
        (lambda d: None, {**VALUES, LINK_REF: "  "}),  # dato vacío
    ],
    ids=["valor_en_campo_de_pago", "valor_en_texto_libre", "dato_sin_referencia", "dato_vacio"],
)
def test_documents_that_would_expose_or_lose_payment_data_are_rejected(service, engine, mutate, values):
    service.create_business("panaderia", "Panadería")
    document = _document()
    mutate(document)
    with pytest.raises(BusinessConfigError):
        service.save_changes("panaderia", document, payment_values=values)
    assert service.history("panaderia") == []
    with engine.connect() as conn:
        assert conn.execute(select(business_config_secrets)).all() == []


def test_without_the_right_key_nothing_is_saved_or_read(service, engine, monkeypatch):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    service.publish("panaderia", 1)

    monkeypatch.setenv(SECRETS_KEY_ENV, Fernet.generate_key().decode())
    with pytest.raises(SecretResolutionError):
        _payment_block(service, engine, "panaderia")

    monkeypatch.delenv(SECRETS_KEY_ENV)
    with pytest.raises(SecretResolutionError):
        service.save_changes("panaderia", _document(), payment_values=VALUES)
    assert len(service.history("panaderia")) == 1


def test_import_script_requires_the_key_and_never_prints_payment_data(tmp_path, monkeypatch, capsys):
    path = tmp_path / "cli.sqlite3"
    url = f"sqlite:///{path.as_posix()}"
    module = _load_script()
    monkeypatch.setenv("BUSINESS_CONFIG_DATABASE_URL", url)
    monkeypatch.setattr("sys.argv", ["init", "--import-tenants"])
    monkeypatch.delenv(SECRETS_KEY_ENV, raising=False)
    assert module.main() == 1
    assert SECRETS_KEY_ENV in capsys.readouterr().out
    assert not path.exists(), "sin clave no se crea la base"

    monkeypatch.setenv(SECRETS_KEY_ENV, Fernet.generate_key().decode())
    assert module.main() == 0
    output = capsys.readouterr().out
    assert f"importados={len(TENANTS)}" in output
    config_service = ConfigService()
    values = {value for slug in TENANTS for value in payment_values(loader._load_legacy_sections(config_service, slug))}
    assert [value for value in values if value in output] == []


# ---------------------------------------------------------------------------
# Desacoplado del almacenamiento
# ---------------------------------------------------------------------------

def test_saving_rejects_documents_that_depend_on_the_yaml(service):
    service.create_business("panaderia", "Panadería")
    document = _document()
    document["payments"][0]["link"]["secret_ref"] = "legacy_yaml:pricing.catalog.payment.link"
    with pytest.raises(BusinessConfigError, match="almacén cifrado"):
        service.save_changes("panaderia", document, payment_values={PHONE_REF: VALUES[PHONE_REF]})
    with pytest.raises(BusinessConfigError, match="almacén cifrado"):
        service.create_business("cafe", "Café", document={**document, "tenant_slug": "cafe"}, payment_values={PHONE_REF: VALUES[PHONE_REF]})
    assert service.history("panaderia") == []
    assert [item.slug for item in service.list_businesses()] == ["panaderia"], "un documento rechazado no deja un negocio a medias"


def test_a_stored_payment_value_cannot_be_written_in_clear_later(service, engine):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    document = _stored_document(service, "panaderia")
    document["sales"]["instructions"] = [f"Paga por Nequi al {VALUES[PHONE_REF]}"]
    with pytest.raises(BusinessConfigError, match="valor de un dato de pago"):
        service.save_changes("panaderia", document)  # aunque esta vez no se envíen datos de pago
    assert len(service.history("panaderia")) == 1
    # Tampoco en los ajustes técnicos.
    settings = {"tenant_slug": "panaderia", "legacy": {"config": {"nota": VALUES[LINK_REF]}}}
    with pytest.raises(BusinessConfigError, match="valor de un dato de pago"):
        service.save_engine_settings("panaderia", settings)


def test_validation_errors_do_not_expose_the_rejected_value(service):
    service.create_business("panaderia", "Panadería")
    document = _document()
    document["payments"][0]["link"] = "https://pagos.ejemplo/escrito-en-claro"
    with pytest.raises(BusinessConfigError) as error:
        service.save_changes("panaderia", document, payment_values={PHONE_REF: VALUES[PHONE_REF]})
    assert "escrito-en-claro" not in "".join(traceback.format_exception(error.value))
    with pytest.raises(ValueError) as direct:
        BusinessConfig.model_validate(document)
    assert "escrito-en-claro" not in str(direct.value)


def test_database_errors_do_not_expose_query_parameters(engine):
    assert engine.hide_parameters is True
    with pytest.raises(IntegrityError) as error, engine.begin() as conn:
        conn.execute(
            business_config_secrets.insert().values(
                tenant_id=uuid.uuid4(), ref_key="dato", ciphertext="texto-cifrado-de-prueba"
            )
        )
    assert "texto-cifrado-de-prueba" not in str(error.value)


def test_payment_references_do_not_grow_with_each_edit(service):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    seen = set()
    for number in range(3):
        document = _stored_document(service, "panaderia")
        holder = document["payments"][0]["link"]
        seen.add(holder["secret_ref"])
        service.save_changes("panaderia", document, payment_values={holder["secret_ref"]: f"https://pagos.ejemplo/{number}"})
    latest = _stored_document(service, "panaderia")["payments"][0]["link"]["secret_ref"]
    assert latest not in seen and latest.count("~") == 1 and latest.startswith(LINK_REF + "~")


def test_each_version_compiles_with_its_own_payment_data(service):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    service.save_changes("panaderia", _document(), payment_values={LINK_REF: "https://pagos.ejemplo/segundo", PHONE_REF: "3000000002"})
    link_of = lambda version: service.compile_sections("panaderia", version)["pricing"]["catalog"]["payment"]["link"]  # noqa: E731
    assert link_of(1) == VALUES[LINK_REF] and link_of(2) == "https://pagos.ejemplo/segundo"
    with pytest.raises(BusinessConfigError):
        service.compile_sections("panaderia")  # nada publicado todavía
    service.publish("panaderia", 2)
    assert service.compile_sections("panaderia")["pricing"]["catalog"]["payment"]["link"] == "https://pagos.ejemplo/segundo"


def test_simultaneous_saves_are_all_kept(service):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    base = _stored_document(service, "panaderia")
    errors: list[str] = []

    def _save(worker: int) -> None:
        for number in range(5):
            edited = copy.deepcopy(base)
            edited["identity"]["description"] = f"hilo {worker}, edición {number}"
            try:
                service.save_changes("panaderia", edited, created_by=f"hilo{worker}")
            except Exception as exc:  # noqa: BLE001
                errors.append(type(exc).__name__)

    threads = [threading.Thread(target=_save, args=(worker,)) for worker in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    history = service.history("panaderia")
    assert [item.version for item in history] == list(range(1, 22)), "ningún guardado se pierde ni repite versión"
    saved = {service.get_version("panaderia", item.version).config.identity.description for item in history[1:]}
    assert len(saved) == 20


def test_listing_survives_a_damaged_version_and_reading_it_is_rejected(service, engine):
    service.create_business("panaderia", "Panadería", document=_document(name="Pan y Café"), payment_values=VALUES)
    service.create_business("cafe", "Café", document=_document("cafe", name="Café Central"), payment_values=VALUES)
    with engine.begin() as conn:
        tenant_id = conn.execute(select(tenants.c.id).where(tenants.c.slug == "panaderia")).scalar_one()
        conn.execute(business_configs.update().where(business_configs.c.tenant_id == tenant_id).values(document={"tenant_slug": "panaderia"}))
    assert [(item.slug, item.name) for item in service.list_businesses()] == [("cafe", "Café Central"), ("panaderia", "Panadería")]
    with pytest.raises(BusinessConfigError):
        service.get_version("panaderia", 1)


def test_dates_are_returned_in_utc(service):
    service.create_business("panaderia", "Panadería", document=_document(), payment_values=VALUES)
    service.publish("panaderia", 1)
    version = service.history("panaderia")[0]
    assert version.created_at.tzinfo == timezone.utc and version.published_at.tzinfo == timezone.utc


# ---------------------------------------------------------------------------
# Migración inicial: segura ante fallos
# ---------------------------------------------------------------------------

def test_import_writes_nothing_if_any_business_cannot_be_prepared(service, monkeypatch):
    original = legacy_store_migration.prepare_tenant

    def _fail_on_saas(config_service, slug):
        if slug == "saas":
            raise BusinessConfigError("saas: no se puede preparar")
        return original(config_service, slug)

    monkeypatch.setattr(legacy_store_migration, "prepare_tenant", _fail_on_saas)
    with pytest.raises(BusinessConfigError):
        import_all(service, ConfigService())
    assert service.list_businesses() == []


def test_import_writes_nothing_without_the_key(service, monkeypatch):
    monkeypatch.delenv(SECRETS_KEY_ENV)
    with pytest.raises(SecretResolutionError):
        import_all(service, ConfigService())
    assert service.list_businesses() == []


def test_import_completes_a_business_left_without_versions_and_reports_one_left_unpublished(service):
    # Un fallo a mitad de una importación anterior: registrado sin versiones se completa; con versiones no se toca.
    service.create_business("clinic", "Registro incompleto")
    document = _document("saas", name="Borrador propio de saas")
    service.create_business("saas", "Saas", document=document, payment_values=VALUES)

    report = import_all(service, ConfigService())
    assert "clinic" in report.created and "saas" not in report.created
    assert report.skipped == ["saas"] and report.unpublished == ["saas"]
    assert service.get_published("clinic").identity.name == "Agenda Clinica Pro"
    assert service.get_draft("saas").config.identity.name == "Borrador propio de saas"
    assert len(service.history("saas")) == 1


def test_a_city_that_differs_from_the_location_is_not_lost_silently():
    """`business.city` solo se unifica si es el mismo dato; si no, la migración se detiene."""
    sections = copy.deepcopy(loader._load_legacy_sections(ConfigService(), "demo"))
    sections["business"]["city"] = "Otra ciudad"
    result = import_legacy_sections("demo", sections)
    assert result.engine_settings.legacy["business"]["city"] == "Otra ciudad"
    with pytest.raises(ValueError, match="conflicto"):
        compile_business_config(result.config, lambda ref: "valor")


@pytest.mark.parametrize("slug", TENANTS)
def test_migration_reads_the_same_sections_as_the_engine(slug):
    service = ConfigService()
    assert legacy_store_migration.read_tenant_sections(service, slug) == loader._load_legacy_sections(service, slug)


def test_import_detects_a_preparation_that_does_not_reproduce_the_yaml(monkeypatch):
    monkeypatch.setattr(legacy_store_migration, "compile_business_config", lambda config, resolve: {})
    with pytest.raises(BusinessConfigError, match="no reproduce"):
        prepare_tenant(ConfigService(), "demo")


# ---------------------------------------------------------------------------
# Ubicación de la base
# ---------------------------------------------------------------------------

def test_database_location_comes_from_its_own_variable_and_not_from_the_engine_database(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://base-del-motor/no-se-usa")
    own = tmp_path / "propia" / "base.sqlite3"
    monkeypatch.setenv(business_config_database.DATABASE_URL_ENV, f"sqlite:///{own.as_posix()}")
    engine = create_business_config_engine()
    assert Path(engine.url.database) == own and own.parent.is_dir()
    engine.dispose()

    monkeypatch.delenv(business_config_database.DATABASE_URL_ENV)
    default = tmp_path / "por_defecto" / "base.sqlite3"
    monkeypatch.setattr(business_config_database, "DEFAULT_LOCAL_DATABASE", default)
    engine = create_business_config_engine()
    assert engine.dialect.name == "sqlite" and Path(engine.url.database) == default
    engine.dispose()


def test_service_depends_only_on_the_storage_ports(engine):
    assert isinstance(BusinessConfigRepository(engine), BusinessConfigStorage)
    assert isinstance(PaymentSecretStore(engine), PaymentSecretStorage)
    source = inspect.getsource(business_config_service)
    assert "sqlalchemy" not in source and "infrastructure" not in source


def test_service_works_with_any_storage_implementing_the_ports():
    """Otra implementación de los puertos sirve sin tocar el servicio: lo que permite pasar a PostgreSQL."""

    class MemoryStorage:
        def __init__(self):
            self.saved = []

        def save_draft(self, tenant_slug, document, *, created_by=None, expected_version=None, payment_secrets=None):
            self.saved.append((tenant_slug, copy.deepcopy(document), dict(payment_secrets or {})))
            return "versión guardada"

    class MemorySecrets:
        def known_values(self, tenant_slug):
            return []

    storage = MemoryStorage()
    result = business_config_service.BusinessConfigService(storage, MemorySecrets()).save_changes("panaderia", _document(), payment_values=VALUES)
    assert result == "versión guardada"
    _slug, document, secrets = storage.saved[0]
    assert sorted(secrets.values()) == sorted(VALUES.values())
    assert {holder["secret_ref"] for holder in iter_secret_refs(document)} == set(secrets)


def test_postgres_schema_comes_from_the_reviewed_migration():
    class FakeEngine:
        class dialect:  # noqa: N801
            name = "postgresql"

    with pytest.raises(ValueError):
        create_local_schema(FakeEngine())
    assert {"tenants", "business_configs", "business_config_secrets", "business_engine_settings"} == set(metadata.tables)
