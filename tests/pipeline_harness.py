"""Ejecución del pipeline real con memoria en RAM y LLM simulado, compartida por las pruebas del contrato."""
from __future__ import annotations

import builtins
import copy
import dataclasses
import functools
import io
import json
from collections.abc import Callable
from pathlib import Path

from cryptography.fernet import Fernet

from app.application.ai_pipeline import AIPipeline
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.payment_data import iter_secret_refs
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.business_config import runtime_access
from app.infrastructure.business_config.database import (
    DATABASE_URL_ENV,
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.example_businesses import ExampleBusiness, import_example, load_example
from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV
from app.infrastructure.persistence.memory_repository import MemoryRepository

# Antes se llamaba así: un negocio de ejemplo listo para el almacén.
PreparedTenant = ExampleBusiness

TENANTS_DIR = Path(__file__).resolve().parents[1] / "project" / "config" / "tenants"

TENANTS = [
    "agencia_viajes", "asesor_ai_prod", "clinic", "demo", "ecommerce",
    "escuela_conduccion", "restaurant", "saas", "tienda_ropa",
]


def forbid_examples_folder(monkeypatch) -> None:
    """Abrir cualquier archivo de la carpeta de ejemplos hace fallar la prueba: el motor solo lee lo publicado en el almacén."""
    examples = TENANTS_DIR.resolve()
    real_open = io.open

    def _guarded(file, *args, **kwargs):
        if isinstance(file, (str, Path)) and Path(file).resolve().is_relative_to(examples):
            raise AssertionError(f"el motor abrió {file}")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(io, "open", _guarded)
    monkeypatch.setattr(builtins, "open", _guarded)


def reply(text: str, intent: str = "info", **metadata) -> str:
    """Respuesta del LLM simulado en el formato estructurado que espera el motor."""
    return json.dumps({"response": text, "intent": intent, "metadata": metadata}, ensure_ascii=False)


def reads(wants: bool = False, method: str = "", paid: bool = False) -> dict:
    """Lo que entiende el lector de pagos simulado del mensaje del cliente (`payment_reading.py`): si debe recibir los datos de pago,
    de qué medio y si dice que ya pagó."""
    return {"recibe_datos_de_pago": wants, "medio": method, "dice_que_ya_pago": paid}


def run_conversation(slug: str, turns: list[tuple], *, user_id: str, with_context: bool = False) -> list[tuple]:
    """Ejecuta el pipeline real turno a turno; devuelve (prompts enviados al asesor, respuesta final) por turno, o con `with_context`
    (respuesta final, lo que el motor decide del chat).

    Cada turno es (mensaje del cliente, respuesta del asesor simulado) y, opcional, lo que entiende el lector de pagos simulado
    (`reads(...)`). Sin lector, el motor confía en la acción del asesor, como cuando la llamada del lector falla. La respuesta del
    asesor puede ser una lista: la primera respuesta y la que da cuando el motor le pide otra."""
    pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()))
    results = []
    for message, llm_reply, *rest in turns:
        prompts: list[str] = []
        replies = list(llm_reply) if isinstance(llm_reply, (list, tuple)) else [llm_reply]
        reading = rest[0] if rest else None

        def _generate(prompt, *, user_message, bot_config=None, _replies=replies, _prompts=prompts, **_kwargs):
            _prompts.append(str(prompt))
            return _replies[min(len(_prompts), len(_replies)) - 1]

        def _classify(prompt, *, user_message, bot_config=None, _reading=reading, **_kwargs):
            if _reading is None:
                raise RuntimeError("sin lector de pagos")
            return json.dumps(_reading, ensure_ascii=False)

        pipeline.runtime.generate = _generate
        pipeline.runtime.classify = _classify
        response, _ai_used, meta = pipeline.run(
            tenant=type("T", (), {"slug": slug, "name": slug, "id": slug})(),
            user_message=message,
            user_id=user_id,
            bot_config=None,
            conversation_history=[],
            faq_results=[],
            yaml_config=None,
            include_metadata=True,
        )
        results.append((response, meta if isinstance(meta, dict) else {}) if with_context else (prompts, response))
    return results


@functools.lru_cache(maxsize=None)
def prepared_tenant(slug: str) -> PreparedTenant:
    """Un negocio de ejemplo listo para el almacén (`project/config/tenants/<slug>/business-config.json`)."""
    return load_example(slug)


GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


@functools.lru_cache(maxsize=None)
def _golden(slug: str) -> str:
    return (GOLDEN_DIR / f"{slug}.json").read_text(encoding="utf-8")


def engine_sections(slug: str) -> dict:
    """La referencia congelada de lo que recibe el motor de ese negocio (lo que tenían sus YAML; ver `tests/golden/README.md`)."""
    return json.loads(_golden(slug))


def stored_document(slug: str) -> dict:
    """El documento que tiene publicado ese negocio en el almacén de la suite (una copia: modificarla no lo cambia)."""
    return copy.deepcopy(prepared_tenant(slug).document)


def publish_store(monkeypatch, tmp_path: Path, tenants: list[PreparedTenant]) -> str:
    """Un almacén solo para esta prueba con esos negocios publicados, y el motor apuntando a él. Devuelve su URL."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{(tmp_path / 'almacen.sqlite3').as_posix()}"
    key = Fernet.generate_key().decode()
    engine = create_business_config_engine(url)
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key=key)
    for tenant in tenants:
        import_example(service, tenant)
    engine.dispose()
    monkeypatch.setenv(DATABASE_URL_ENV, url)
    monkeypatch.setenv(SECRETS_KEY_ENV, key)
    runtime_access.dispose_shared_engines()
    return url


def publish_document(monkeypatch, tmp_path: Path, slug: str, mutate: Callable[[dict], object] | None = None, *, engine_settings: dict | None = None, as_slug: str | None = None) -> str:
    """Publica el negocio con su documento modificado en un almacén propio de la prueba, como lo haría el panel.

    `as_slug` lo publica con otro identificador (un negocio nuevo, sin carpeta de ejemplo)."""
    tenant = prepared_tenant(slug)
    document = copy.deepcopy(tenant.document)
    if as_slug:
        document["tenant_slug"] = as_slug
    if mutate is not None:
        mutate(document)
    BusinessConfig.model_validate(document)
    refs = {holder["secret_ref"] for holder in iter_secret_refs(document)}
    values = {ref: value for ref, value in tenant.payment_values.items() if ref in refs}
    settings = {**copy.deepcopy(tenant.engine_settings), **(engine_settings or {})}
    if as_slug:
        settings["tenant_slug"] = as_slug
    changed = dataclasses.replace(tenant, slug=as_slug or slug, document=document, payment_values=values, engine_settings=settings)
    return publish_store(monkeypatch, tmp_path, [changed])


def run_with_document(monkeypatch, tmp_path: Path, slug: str, mutate: Callable[[dict], object], turns, *, user_id: str = "opciones"):
    """Publica el negocio con su documento modificado y ejecuta el pipeline real, que lo lee del almacén."""
    publish_document(monkeypatch, tmp_path, slug, mutate)
    return run_conversation(slug, turns, user_id=user_id)
