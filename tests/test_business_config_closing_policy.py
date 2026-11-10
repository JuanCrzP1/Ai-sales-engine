"""
Definición común del cierre: cinco valores iguales para todos los negocios.

Están fuera del contrato comercial y de los ajustes técnicos, en `COMMON_CLOSING_POLICY`. El compilador los añade a
`sales.closing`, de modo que el motor recibe lo mismo que tenían los YAML de origen, y el importador rechaza un YAML con
otros valores. Estas pruebas no modifican los YAML: los que cambian son copias temporales.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml
from cryptography.fernet import Fernet
from pydantic import ValidationError

from app.application.ai_pipeline import AIPipeline
from app.application.runtime import load_tenant_runtime_yaml
from app.domain.business_config.compiler import comparable_with_yaml, compile_business_config
from app.domain.business_config.contract import BusinessConfig, Closing
from app.domain.business_config.engine_policy import COMMON_CLOSING_POLICY
from app.domain.business_config.engine_settings import EngineSettings
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.config import legacy_store_migration
from app.infrastructure.config.business_config_store import BusinessConfigStore
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_field_catalog import contract_fields
from app.infrastructure.config.legacy_store_migration import import_all, import_prepared, prepare_tenant, read_tenant_sections
from app.infrastructure.config.legacy_yaml_importer import import_legacy_sections
from app.infrastructure.config.payment_secrets import LegacyYamlSecretResolver
from app.infrastructure.persistence.memory_repository import MemoryRepository
from pipeline_harness import TENANTS, TENANTS_DIR, reply

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "project" / "config" / "contracts" / "v1" / "business-config.schema.json"
EXPECTED = {
    "next_step": {"action": "dynamic"},
    "behavior": {
        "direct_sale": {"goal": "confirmar_compra"},
        "lead_capture": {"goal": "capturar_datos"},
        "booking": {"goal": "agendar"},
        "checkout": {"goal": "enviar_pago"},
    },
}
CONVERSATION = [
    ("Hola, necesito información", reply("Claro.")),
    ("¿Cuánto cuesta?", reply("Te cuento los precios.")),
    ("Quiero comprar, ¿cómo cierro?", reply("Listo.", "buy")),
    ("Quiero pagar por Nequi", reply("Listo.", "buy", payment_method="nequi")),
]


def _sections(slug: str) -> dict:
    return read_tenant_sections(ConfigService(), slug)


def _raw_closing(slug: str) -> dict:
    """Leído directamente del YAML, sin pasar por ningún código del proyecto."""
    return yaml.safe_load((TENANTS_DIR / slug / "sales.yaml").read_text(encoding="utf-8"))["sales"]["closing"]


def _compile_from_files(slug: str, config: BusinessConfig | None = None) -> dict:
    sections = _sections(slug)
    config = config if config is not None else BusinessConfigStore(ConfigService().tenants_root).load(slug)
    return compile_business_config(config, LegacyYamlSecretResolver(lambda: sections))


def _document(slug: str) -> dict:
    return json.loads(BusinessConfigStore(ConfigService().tenants_root).path_for(slug).read_text(encoding="utf-8"))


@pytest.fixture
def service(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'base.sqlite3').as_posix()}")
    create_local_schema(engine)
    yield build_business_config_service(engine, secrets_key=Fernet.generate_key().decode())
    engine.dispose()


# ---------------------------------------------------------------------------
# Un solo lugar y los cinco valores conservados
# ---------------------------------------------------------------------------

def test_the_five_values_are_defined_in_a_single_module():
    assert COMMON_CLOSING_POLICY == EXPECTED
    owners = {
        path.name
        for path in (ROOT_DIR / "project" / "app").rglob("*.py")
        if "confirmar_compra" in path.read_text(encoding="utf-8", errors="ignore") or "capturar_datos" in path.read_text(encoding="utf-8", errors="ignore")
    }
    assert owners == {"engine_policy.py"}


@pytest.mark.parametrize("slug", TENANTS)
def test_each_business_keeps_the_five_values(service, slug):
    closing = _raw_closing(slug)
    assert {key: closing[key] for key in EXPECTED} == EXPECTED, "los YAML ya tienen estos valores"

    from_files = _compile_from_files(slug)["sales"]["closing"]
    assert {key: from_files[key] for key in EXPECTED} == EXPECTED

    import_prepared(service, prepare_tenant(ConfigService(), slug))
    from_store = service.compile_sections(slug)["sales"]["closing"]
    assert {key: from_store[key] for key in EXPECTED} == EXPECTED


@pytest.mark.parametrize("slug", TENANTS)
def test_compilation_has_the_same_structure_as_the_yaml(slug):
    compiled = _compile_from_files(slug)
    # Más el perfil comercial, que los YAML no tienen.
    assert comparable_with_yaml(compiled) == _sections(slug)
    # También el mismo orden de claves: los metadatos internos del motor llevan esta sección tal cual.
    assert json.dumps(compiled["sales"]["closing"], ensure_ascii=False) == json.dumps(_raw_closing(slug), ensure_ascii=False)


def test_compiled_values_are_copies_of_the_policy():
    compiled = _compile_from_files("saas")["sales"]["closing"]
    compiled["next_step"]["action"] = "cambiado"
    compiled["behavior"]["booking"]["goal"] = "cambiado"
    assert COMMON_CLOSING_POLICY == EXPECTED
    assert _compile_from_files("saas")["sales"]["closing"]["next_step"] == EXPECTED["next_step"]


# ---------------------------------------------------------------------------
# No son opciones editables del contrato comercial
# ---------------------------------------------------------------------------

def test_the_values_are_not_fields_of_the_commercial_contract():
    assert set(Closing.model_fields) == {"strategy", "required_data", "purchase_signals", "high_intent_actions", "next_steps", "micro_commitments", "rules"}
    closing_paths = {path for path in contract_fields(json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))) if path.startswith("sales.closing.")}
    assert not [path for path in closing_paths if path.rsplit(".", 1)[-1] in {"behavior", "next_step", "goal", "action"} or ".behavior." in path or ".next_step." in path]
    panel_types = (ROOT_DIR / "apps" / "admin-web" / "src" / "contracts" / "businessConfig.v1.ts").read_text(encoding="utf-8")
    closing_type = panel_types.split("export interface Closing {", 1)[1].split("\n}", 1)[0]
    assert "behavior" not in closing_type and "next_step?" not in closing_type and "goal" not in closing_type


@pytest.mark.parametrize("key", list(EXPECTED))
def test_a_document_cannot_carry_the_values(key):
    document = _document("saas")
    document["sales"]["closing"][key] = EXPECTED[key]
    with pytest.raises(ValidationError):
        BusinessConfig.model_validate(document)


@pytest.mark.parametrize("slug", TENANTS)
def test_the_values_are_outside_both_documents(slug):
    store = BusinessConfigStore(ConfigService().tenants_root)
    document, settings = _document(slug), json.loads(store.engine_settings_path_for(slug).read_text(encoding="utf-8"))
    assert not set(EXPECTED) & set(document["sales"]["closing"])
    assert "closing" not in settings.get("legacy", {}).get("sales", {})


# ---------------------------------------------------------------------------
# Los valores divergentes se rechazan
# ---------------------------------------------------------------------------

DIVERGENCES = {
    "objetivo_de_venta_directa": lambda c: c["behavior"]["direct_sale"].update(goal="otro"),
    "objetivo_de_captacion": lambda c: c["behavior"]["lead_capture"].update(goal="otro"),
    "objetivo_de_reserva": lambda c: c["behavior"]["booking"].update(goal="otro"),
    "objetivo_de_pago": lambda c: c["behavior"]["checkout"].update(goal="otro"),
    "accion_del_siguiente_paso": lambda c: c["next_step"].update(action="fixed"),
    "sin_objetivos": lambda c: c.pop("behavior"),
    "sin_siguiente_paso": lambda c: c.pop("next_step"),
    "objetivo_sin_valor": lambda c: c["behavior"]["booking"].pop("goal"),
    "tipo_de_cierre_adicional": lambda c: c["behavior"].update(otro={"goal": "otro"}),
    "campo_adicional_en_el_siguiente_paso": lambda c: c["next_step"].update(modo="otro"),
}


def _diverged_sections(case: str, slug: str = "demo") -> dict:
    sections = copy.deepcopy(_sections(slug))
    DIVERGENCES[case](sections["sales"]["closing"])
    return sections


@pytest.mark.parametrize("case", DIVERGENCES)
def test_divergent_values_are_rejected_on_import(case):
    with pytest.raises(ValueError, match="política global"):
        import_legacy_sections("demo", _diverged_sections(case))


@pytest.mark.parametrize("case", ["objetivo_de_reserva", "accion_del_siguiente_paso", "sin_objetivos"])
def test_a_divergent_business_stops_the_migration_without_writing_anything(service, monkeypatch, case):
    original = legacy_store_migration.read_tenant_sections

    def _read(config_service, slug):
        return _diverged_sections(case, slug) if slug == "saas" else original(config_service, slug)

    monkeypatch.setattr(legacy_store_migration, "read_tenant_sections", _read)
    with pytest.raises(ValueError, match="política global"):
        import_all(service, ConfigService())
    assert service.list_businesses() == []


def test_the_documents_script_reports_a_divergent_business(monkeypatch):
    spec = importlib.util.spec_from_file_location("migrate_tenants_to_contract", ROOT_DIR / "scripts" / "migrate_tenants_to_contract.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = module.read_tenant_sections

    def _read(config_service, slug):
        if slug != "saas":
            return original(config_service, slug)
        sections = copy.deepcopy(original(config_service, slug))
        sections["sales"]["closing"]["next_step"]["action"] = "fixed"
        return sections

    monkeypatch.setattr(module, "read_tenant_sections", _read)
    documents, _report, errors = module.build()
    assert [slug for slug, _message in errors] == ["saas"]
    assert not [path for path in documents if path.parent.name == "saas"]


def test_legacy_settings_cannot_override_the_policy():
    settings = {"tenant_slug": "saas", "legacy": {"sales": {"closing": {"next_step": {"action": "fixed"}}}}}
    config = BusinessConfig.model_validate(_document("saas")).with_engine_settings(EngineSettings.model_validate(settings))
    with pytest.raises(ValueError, match="conflicto"):
        compile_business_config(config, lambda ref: "valor")


# ---------------------------------------------------------------------------
# El comportamiento del motor no cambia
# ---------------------------------------------------------------------------

def _run_with_metadata(slug: str, *, user_id: str, runtime_loader=None) -> list[tuple[list[str], str, dict]]:
    pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()), runtime_loader=runtime_loader)
    results = []
    for message, llm_reply in CONVERSATION:
        prompts: list[str] = []

        def _generate(prompt, *, user_message, bot_config=None, _reply_text=llm_reply, _prompts=prompts, **_kwargs):
            _prompts.append(str(prompt))
            return _reply_text

        pipeline.runtime.generate = _generate
        response, _ai_used, metadata = pipeline.run(
            tenant=type("T", (), {"slug": slug, "name": slug, "id": slug})(),
            user_message=message,
            user_id=user_id,
            bot_config=None,
            conversation_history=[],
            faq_results=[],
            yaml_config=None,
            include_metadata=True,
        )
        results.append((prompts, response, metadata))
    return results


@pytest.mark.parametrize("slug", TENANTS)
def test_the_engine_receives_the_common_policy_from_what_was_published(slug):
    """Lo publicado llega al motor con los cinco valores de la definición común, iguales a los de sus YAML de origen."""
    runtime = load_tenant_runtime_yaml(slug)
    closing = runtime["sales"].get("closing")
    if "closing" not in _raw_closing_section(slug):
        assert closing is None
        return
    assert {key: closing[key] for key in EXPECTED} == EXPECTED
    for _prompts, _response, metadata in _run_with_metadata(slug, user_id="politica"):
        assert {key: metadata["sales"]["closing"][key] for key in EXPECTED} == EXPECTED


def _raw_closing_section(slug: str) -> dict:
    return yaml.safe_load((TENANTS_DIR / slug / "sales.yaml").read_text(encoding="utf-8"))["sales"]


def _set_markers(closing: dict) -> None:
    for name, value in closing["behavior"].items():
        value["goal"] = f"marca_{name}"
    closing["next_step"]["action"] = "marca_de_accion"


def _remove(closing: dict) -> None:
    del closing["behavior"]
    del closing["next_step"]


@pytest.mark.parametrize("change", [_set_markers, _remove], ids=["valores_cambiados", "valores_quitados"])
@pytest.mark.parametrize("slug", TENANTS)
def test_the_values_do_not_influence_prompts_or_replies(slug, change):
    """Sustituirlos o quitarlos del runtime no cambia nada: el motor no decide con ellos."""
    runtime = load_tenant_runtime_yaml(slug)
    if not isinstance(runtime["sales"].get("closing"), dict):
        pytest.skip("este negocio no tiene sección de cierre")
    changed_runtime = copy.deepcopy(runtime)
    change(changed_runtime["sales"]["closing"])
    original = _run_with_metadata(slug, user_id="politica")
    changed = _run_with_metadata(slug, user_id="politica", runtime_loader=lambda _slug, **_options: copy.deepcopy(changed_runtime))
    assert [(prompts, response) for prompts, response, _metadata in changed] == [(prompts, response) for prompts, response, _metadata in original]
    assert "marca_" not in json.dumps([(prompts, response) for prompts, response, _metadata in changed], ensure_ascii=False)


# ---------------------------------------------------------------------------
# Las capacidades comerciales variables no se alteran
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("strategy", ["direct_sale", "lead_capture", "booking", "checkout"])
@pytest.mark.parametrize("slug", TENANTS)
def test_variable_closing_fields_stay_under_the_control_of_each_business(slug, strategy):
    document = _document(slug)
    closing = document["sales"]["closing"]
    closing.update(strategy=strategy, required_data=["dato_propio"], purchase_signals=["señal propia"], next_steps=["paso propio"], rules=["regla propia"])
    expected = copy.deepcopy(_sections(slug))
    expected["sales"]["closing"].update(strategy=strategy, required_data=["dato_propio"], triggers=["señal propia"], next_steps=["paso propio"], hard_rules=["regla propia"])

    settings = BusinessConfigStore(ConfigService().tenants_root).load_engine_settings(slug)
    compiled = _compile_from_files(slug, BusinessConfig.model_validate(document).with_engine_settings(settings))
    assert comparable_with_yaml(compiled) == expected
    assert {key: compiled["sales"]["closing"][key] for key in EXPECTED} == EXPECTED, "la definición común no depende del tipo de cierre elegido"


def test_a_business_without_closing_section_does_not_receive_the_policy():
    document = _document("saas")
    del document["sales"]["closing"]
    compiled = compile_business_config(BusinessConfig.model_validate(document), lambda ref: "valor")
    assert "closing" not in compiled["sales"]
