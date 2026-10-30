"""
Almacén de configuración en base de datos: versiones, publicación, reversión, datos de pago cifrados
y su uso por el runtime (`BUSINESS_CONFIG_STORE=database`).

Se ejecuta sobre SQLite en memoria con las mismas tablas que la migración
`project/db/migrations/0001_business_config_store.sql`; no se conecta a Neon ni a PostgreSQL, por lo
que no prueba particularidades de PostgreSQL (JSONB, índices parciales en el servidor real).
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool

from app.application.pipeline.ai_execution import ejecutar_pago
from app.application.runtime import load_tenant_runtime_yaml
from app.application.runtime import tenant_runtime_loader as loader
from app.domain.business_config.compiler import compile_business_config
from app.infrastructure.config.business_config_repository import BusinessConfigRepository
from app.infrastructure.config.business_config_store import BusinessConfigError, BusinessConfigStore
from app.infrastructure.config.business_config_tables import business_config_secrets, business_configs, metadata, tenants
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.payment_secret_store import SECRETS_KEY_ENV, PaymentSecretStore
from app.infrastructure.config.payment_secrets import SecretResolutionError

ROOT_DIR = Path(__file__).resolve().parents[1]
MIGRATION = ROOT_DIR / "project" / "db" / "migrations" / "0001_business_config_store.sql"
ENGINE_SCHEMA = ROOT_DIR / "project" / "docs" / "postgresql_schema.sql"


@pytest.fixture
def engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    metadata.create_all(engine)
    with engine.begin() as conn:
        for slug in ("restaurant", "saas"):
            conn.execute(tenants.insert().values(id=uuid.uuid4(), slug=slug))
    return engine


def _document(slug: str) -> dict:
    return json.loads(BusinessConfigStore(ConfigService().tenants_root).path_for(slug).read_text(encoding="utf-8"))


def _with_length(document: dict, length: str) -> dict:
    return {**document, "response_style": {**document["response_style"], "length": length, "max_words": None}}


# ---------------------------------------------------------------------------
# Versiones, publicación y reversión
# ---------------------------------------------------------------------------

def test_save_validates_and_creates_immutable_versions(engine):
    repository = BusinessConfigRepository(engine)
    invalid = {**_document("restaurant"), "identity": {"name": "Sin datos obligatorios"}}
    with pytest.raises(BusinessConfigError):
        repository.save_draft("restaurant", invalid)
    with pytest.raises(BusinessConfigError):
        repository.save_draft("restaurant", _document("saas"))  # documento de otro negocio
    with pytest.raises(BusinessConfigError):
        repository.save_draft("tenant_inexistente", _document("restaurant"))
    assert repository.history("restaurant") == []

    first = repository.save_draft("restaurant", _document("restaurant"), created_by="panel")
    second = repository.save_draft("restaurant", _with_length(_document("restaurant"), "long"))
    assert (first.version, second.version) == (1, 2)
    assert first.content_hash != second.content_hash
    assert [(v.version, v.status) for v in repository.history("restaurant")] == [(1, "draft"), (2, "draft")]
    with pytest.raises(BusinessConfigError):
        repository.published("restaurant")


def test_publish_keeps_one_published_version_and_rollback_restores_the_previous(engine):
    repository = BusinessConfigRepository(engine)
    repository.save_draft("restaurant", _with_length(_document("restaurant"), "short"))
    repository.save_draft("restaurant", _with_length(_document("restaurant"), "long"))

    repository.publish("restaurant", 1)
    assert repository.published("restaurant").response_style.length == "short"
    repository.publish("restaurant", 2)
    assert repository.published("restaurant").response_style.length == "long"
    assert [v.status for v in repository.history("restaurant")] == ["archived", "published"]

    assert repository.rollback("restaurant") == 1
    assert repository.published("restaurant").response_style.length == "short"
    assert [v.status for v in repository.history("restaurant")] == ["published", "archived"]
    with pytest.raises(BusinessConfigError):
        repository.rollback("restaurant")  # no hay una versión publicada anterior a la 1


def test_failed_publish_check_leaves_the_published_version_untouched(engine):
    repository = BusinessConfigRepository(engine)
    repository.save_draft("restaurant", _document("restaurant"))
    repository.save_draft("restaurant", _with_length(_document("restaurant"), "long"))
    repository.publish("restaurant", 1)

    def _reject(_config):
        raise SecretResolutionError("falta un dato de pago")

    with pytest.raises(SecretResolutionError):
        repository.publish("restaurant", 2, check=_reject)
    assert [v.status for v in repository.history("restaurant")] == ["published", "draft"]


def test_tenants_are_isolated(engine):
    repository = BusinessConfigRepository(engine)
    repository.save_draft("restaurant", _document("restaurant"))
    repository.save_draft("saas", _document("saas"))
    repository.publish("restaurant", 1)
    repository.publish("saas", 1)
    assert repository.published("restaurant").tenant_slug == "restaurant"
    assert repository.published("saas").tenant_slug == "saas"
    # Publicar otra versión de un negocio no archiva la del otro.
    repository.save_draft("saas", _with_length(_document("saas"), "long"))
    repository.publish("saas", 2)
    assert [v.status for v in repository.history("restaurant")] == ["published"]
    assert repository.published("saas").response_style.length == "long"


def test_stored_document_is_validated_before_use(engine):
    repository = BusinessConfigRepository(engine)
    repository.save_draft("restaurant", _document("restaurant"))
    repository.publish("restaurant", 1)
    tampered = {**_document("restaurant"), "response_style": {"length": "short", "max_words": 500}}
    with engine.begin() as conn:
        conn.execute(update(business_configs).values(document=tampered))
    with pytest.raises(BusinessConfigError):
        repository.published("restaurant")


# ---------------------------------------------------------------------------
# Datos de pago cifrados
# ---------------------------------------------------------------------------

def test_payment_secrets_are_encrypted_and_scoped_to_their_tenant(engine):
    store = PaymentSecretStore(engine, key=Fernet.generate_key().decode())
    store.put_many("restaurant", {"secret_store:principal.transfer.0.number": "3009998877"})
    with engine.connect() as conn:
        ciphertext = conn.execute(select(business_config_secrets.c.ciphertext)).scalar_one()
    assert "3009998877" not in ciphertext

    ref = type("Ref", (), {"secret_ref": "secret_store:principal.transfer.0.number"})()
    assert store.resolver("restaurant")(ref) == "3009998877"
    with pytest.raises(SecretResolutionError):
        store.resolver("saas")(ref)  # otro negocio no puede leerlo
    store.put_many("restaurant", {"secret_store:principal.transfer.0.number": "3001112233"})
    assert store.resolver("restaurant")(ref) == "3001112233"


def test_payment_secrets_require_the_right_key(engine, monkeypatch):
    monkeypatch.delenv(SECRETS_KEY_ENV, raising=False)
    ref = type("Ref", (), {"secret_ref": "secret_store:principal.link"})()
    with pytest.raises(SecretResolutionError):
        PaymentSecretStore(engine).put_many("restaurant", {"secret_store:principal.link": "https://pago"})
    PaymentSecretStore(engine, key=Fernet.generate_key().decode()).put_many("restaurant", {"secret_store:principal.link": "https://pago"})
    with pytest.raises(SecretResolutionError):
        PaymentSecretStore(engine, key=Fernet.generate_key().decode()).resolver("restaurant")(ref)
    with pytest.raises(SecretResolutionError):
        PaymentSecretStore(engine, key="no-es-una-clave").resolver("restaurant")(ref)
    with pytest.raises(SecretResolutionError):
        PaymentSecretStore(engine, key=Fernet.generate_key().decode()).put_many("restaurant", {"legacy_yaml:pricing.x": "1"})


# ---------------------------------------------------------------------------
# El runtime usa la versión publicada (BUSINESS_CONFIG_STORE=database)
# ---------------------------------------------------------------------------

@pytest.fixture
def database_source(engine, monkeypatch):
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "restaurant")
    monkeypatch.setenv(loader.CONTRACT_STORE_ENV, "database")
    monkeypatch.setattr(loader, "get_engine", lambda: engine)
    return BusinessConfigRepository(engine)


def test_runtime_reads_the_published_version_and_follows_rollback(database_source, monkeypatch):
    database_source.save_draft("restaurant", _document("restaurant"))
    database_source.save_draft("restaurant", _with_length(_document("restaurant"), "long"))
    database_source.publish("restaurant", 1)
    from_database = load_tenant_runtime_yaml("restaurant")

    monkeypatch.setenv(loader.CONTRACT_STORE_ENV, "file")
    assert from_database == load_tenant_runtime_yaml("restaurant")  # mismo resultado que el archivo
    monkeypatch.setenv(loader.CONTRACT_STORE_ENV, "database")

    database_source.publish("restaurant", 2)
    assert load_tenant_runtime_yaml("restaurant")["config"]["response"] == {"length": "long", "max_words": 100}
    database_source.rollback("restaurant")
    assert load_tenant_runtime_yaml("restaurant")["config"]["response"] == {"length": "short", "max_words": 60}


def test_runtime_falls_back_to_yaml_without_a_valid_published_version(database_source, engine, monkeypatch):
    errors: list[dict] = []
    monkeypatch.setattr(loader.logger, "error", lambda event, extra=None, **_: errors.append({"event": event, **(extra or {})}))
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV)
    from_yaml = load_tenant_runtime_yaml("restaurant")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "restaurant")

    assert load_tenant_runtime_yaml("restaurant") == from_yaml  # sin versión publicada
    database_source.save_draft("restaurant", _document("restaurant"))
    database_source.publish("restaurant", 1)
    with engine.begin() as conn:
        conn.execute(update(business_configs).values(document={"tenant_slug": "restaurant"}))
    assert load_tenant_runtime_yaml("restaurant") == from_yaml  # versión publicada corrupta
    def _database_down():
        raise OperationalError("SELECT 1", {}, Exception("postgresql://usuario:clave@host/db"))

    monkeypatch.setattr(loader, "get_engine", _database_down)
    assert load_tenant_runtime_yaml("restaurant") == from_yaml  # base de datos caída
    assert [error["event"] for error in errors] == ["business_config_contract_invalid"] * 3
    assert errors[-1]["error"] == "OperationalError" and "clave" not in json.dumps(errors)


def test_panel_document_with_encrypted_payment_data_reaches_the_payment_reply(database_source, engine, monkeypatch):
    """Documento como lo produce el panel: datos de pago en el almacén cifrado, no en el contrato."""
    monkeypatch.setenv(SECRETS_KEY_ENV, Fernet.generate_key().decode())
    document = _document("restaurant")
    document["payments"] = [
        {
            "id": "principal",
            "link": {"secret_ref": "secret_store:principal.link"},
            "transfer_enabled": True,
            "transfer_methods": [{"type": "nequi", "number": {"secret_ref": "secret_store:principal.transfer.0.number"}}],
        }
    ]
    document["offer"]["catalog"]["payment_profile"] = "principal"
    store = PaymentSecretStore(engine)
    version = database_source.save_draft("restaurant", document).version

    def _compiles(config):
        compile_business_config(config, store.resolver("restaurant"))

    with pytest.raises(SecretResolutionError):
        database_source.publish("restaurant", version, check=_compiles)  # aún faltan los datos de pago
    store.put_many("restaurant", {"secret_store:principal.link": "https://pagos.ejemplo/abc", "secret_store:principal.transfer.0.number": "3005556677"})
    database_source.publish("restaurant", version, check=_compiles)

    runtime = load_tenant_runtime_yaml("restaurant")
    assert "3005556677" in ejecutar_pago(runtime, "nequi")
    assert "https://pagos.ejemplo/abc" in ejecutar_pago(runtime, "link")
    with engine.connect() as conn:
        stored_document = json.dumps(conn.execute(select(business_configs.c.document)).scalar_one())
    assert "3005556677" not in stored_document and "pagos.ejemplo" not in stored_document


# ---------------------------------------------------------------------------
# La migración SQL y las tablas de la aplicación coinciden; identificadores UUID
# ---------------------------------------------------------------------------

def _sql_columns(sql: str, table: str) -> dict[str, str]:
    body = re.search(rf"CREATE TABLE IF NOT EXISTS {table} \((.*?)\n\);", sql, re.S).group(1)
    columns = {}
    for line in body.splitlines():
        match = re.match(r"\s+([a-z_]+)\s+([A-Z]+)", line)
        if match and match.group(1) not in {"constraint", "unique", "primary"}:
            columns[match.group(1)] = match.group(2)
    return columns


def test_migration_matches_the_application_tables_and_uses_uuid_tenants():
    sql = MIGRATION.read_text(encoding="utf-8")
    for table in (business_configs, business_config_secrets):
        assert set(_sql_columns(sql, table.name)) == {column.name for column in table.columns}
    assert _sql_columns(sql, "business_configs")["tenant_id"] == "UUID"
    assert _sql_columns(sql, "business_config_secrets")["tenant_id"] == "UUID"
    assert "business_configs_one_published" in sql and "WHERE status = 'published'" in sql
    # El negocio se identifica por UUID en el esquema del motor que referencian las claves foráneas.
    assert re.search(r"CREATE TABLE tenants \(\s*id UUID PRIMARY KEY", ENGINE_SCHEMA.read_text(encoding="utf-8"))
