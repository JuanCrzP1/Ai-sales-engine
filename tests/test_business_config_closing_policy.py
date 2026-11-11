"""
Definición común del cierre: cinco valores iguales para todos los negocios.

Están fuera del contrato comercial y de los ajustes técnicos, en `COMMON_CLOSING_POLICY`. El compilador los añade a
`sales.closing`, de modo que el motor recibe lo mismo que tenían los YAML de origen (la referencia congelada en `tests/golden/`,
en su orden original). Ningún documento ni ajuste técnico puede traerlos ni cambiarlos.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
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
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.config.legacy_field_catalog import contract_fields
from app.infrastructure.persistence.memory_repository import MemoryRepository
from pipeline_harness import TENANTS, engine_sections, reply

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
    return engine_sections(slug)


def _raw_closing(slug: str) -> dict:
    """Lo que el motor recibía de su YAML, con las claves en su orden original."""
    return engine_sections(slug)["sales"]["closing"]


def _compile_from_files(slug: str, config: BusinessConfig | None = None) -> dict:
    example = load_example(slug)
    return compile_business_config(config if config is not None else example.config(), example.payment_resolver())


def _document(slug: str) -> dict:
    return copy.deepcopy(load_example(slug).document)


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
    assert {key: closing[key] for key in EXPECTED} == EXPECTED, "los YAML ya tenían estos valores"

    from_files = _compile_from_files(slug)["sales"]["closing"]
    assert {key: from_files[key] for key in EXPECTED} == EXPECTED

    import_example(service, load_example(slug))
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
    document, settings = _document(slug), load_example(slug).engine_settings
    assert not set(EXPECTED) & set(document["sales"]["closing"])
    assert "closing" not in settings.get("legacy", {}).get("sales", {})


# ---------------------------------------------------------------------------
# Los valores divergentes se rechazan
# ---------------------------------------------------------------------------

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
    return engine_sections(slug)["sales"]


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

    settings = load_example(slug).config().engine_settings
    compiled = _compile_from_files(slug, BusinessConfig.model_validate(document).with_engine_settings(settings))
    assert comparable_with_yaml(compiled) == expected
    assert {key: compiled["sales"]["closing"][key] for key in EXPECTED} == EXPECTED, "la definición común no depende del tipo de cierre elegido"


def test_a_business_without_closing_section_does_not_receive_the_policy():
    document = _document("saas")
    del document["sales"]["closing"]
    compiled = compile_business_config(BusinessConfig.model_validate(document), lambda ref: "valor")
    assert "closing" not in compiled["sales"]
