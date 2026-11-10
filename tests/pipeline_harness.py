"""Ejecución del pipeline real con memoria en RAM y LLM simulado, compartida por las pruebas del contrato."""
from __future__ import annotations

import copy
import dataclasses
import functools
import json
import shutil
from collections.abc import Callable
from pathlib import Path

from cryptography.fernet import Fernet

from app.application.ai_pipeline import AIPipeline
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.payment_data import iter_secret_refs
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.ai.prompting.sections.profile import build_business_profile_context
from app.infrastructure.business_config import runtime_access
from app.infrastructure.business_config.database import (
    DATABASE_URL_ENV,
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_store_migration import PreparedTenant, import_prepared, prepare_tenant
from app.infrastructure.persistence.memory_repository import MemoryRepository

TENANTS_DIR = Path(__file__).resolve().parents[1] / "project" / "config" / "tenants"

TENANTS = [
    "agencia_viajes", "asesor_ai_prod", "clinic", "demo", "ecommerce",
    "escuela_conduccion", "restaurant", "saas", "tienda_ropa",
]


def as_yaml_prompt(prompt: str, runtime: dict) -> str:
    """El prompt del contrato sin lo que solo existe con el contrato: el bloque del perfil comercial (con los datos del negocio en la
    presentación, solo sus reglas en una conversación en curso) y el tono en la línea ESTILO. Lo demás debe ser idéntico a los YAML.
    """
    for include_facts in (True, False):
        block = build_business_profile_context(runtime, include_facts=include_facts)
        if block and f"\n\n{block}\n\n" in prompt:
            prompt = prompt.replace(f"\n\n{block}", "", 1)
            break
    tone = runtime["config"]["profile"].get("tone", "").strip()
    return prompt.replace(f"palabras, {tone}.", "palabras, natural y claro.", 1) if tone else prompt


def reply(text: str, intent: str = "info", **metadata) -> str:
    """Respuesta del LLM simulado en el formato estructurado que espera el motor."""
    return json.dumps({"response": text, "intent": intent, "metadata": metadata}, ensure_ascii=False)


def run_conversation(slug: str, turns: list[tuple[str, str]], *, user_id: str) -> list[tuple[list[str], str]]:
    """Ejecuta el pipeline real turno a turno; devuelve (prompts enviados al LLM, respuesta final) por turno."""
    pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()))
    results = []
    for message, llm_reply in turns:
        prompts: list[str] = []

        def _generate(prompt, *, user_message, bot_config=None, _reply_text=llm_reply, _prompts=prompts):
            _prompts.append(str(prompt))
            return _reply_text

        pipeline.runtime.generate = _generate
        response, _ai_used, _meta = pipeline.run(
            tenant=type("T", (), {"slug": slug, "name": slug, "id": slug})(),
            user_message=message,
            user_id=user_id,
            bot_config=None,
            conversation_history=[],
            faq_results=[],
            yaml_config=None,
            include_metadata=True,
        )
        results.append((prompts, response))
    return results


def copy_tenant(tmp_path: Path, slug: str) -> ConfigService:
    """Copia los YAML de un negocio a un directorio temporal, para probar su importación sin tocar los originales."""
    config_root = tmp_path / "config"
    shutil.copytree(TENANTS_DIR / slug, config_root / "tenants" / slug)
    return ConfigService(base_path=str(config_root))


@functools.lru_cache(maxsize=None)
def prepared_tenant(slug: str) -> PreparedTenant:
    """Un negocio de ejemplo listo para el almacén, como lo importa la migración desde sus YAML."""
    return prepare_tenant(ConfigService(), slug)


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
        import_prepared(service, tenant)
    engine.dispose()
    monkeypatch.setenv(DATABASE_URL_ENV, url)
    monkeypatch.setenv(SECRETS_KEY_ENV, key)
    runtime_access.dispose_shared_engines()
    return url


def publish_document(monkeypatch, tmp_path: Path, slug: str, mutate: Callable[[dict], object] | None = None, *, engine_settings: dict | None = None, as_slug: str | None = None) -> str:
    """Publica el negocio con su documento modificado en un almacén propio de la prueba, como lo haría el panel.

    `as_slug` lo publica con otro identificador (un negocio nuevo, sin carpeta YAML)."""
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
