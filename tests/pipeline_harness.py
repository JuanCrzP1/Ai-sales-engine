"""Ejecución del pipeline real con memoria en RAM y LLM simulado, compartida por las pruebas del contrato."""
from __future__ import annotations

import functools
import json
import shutil
from collections.abc import Callable
from pathlib import Path

import app.application.ai_pipeline as ai_pipeline_module
from app.application.ai_pipeline import AIPipeline
from app.application.runtime import load_tenant_runtime_yaml
from app.application.runtime import tenant_runtime_loader as loader
from app.domain.business_config.contract import BusinessConfig
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.config.business_config_store import BusinessConfigStore
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.persistence.memory_repository import MemoryRepository

TENANTS_DIR = Path(__file__).resolve().parents[1] / "project" / "config" / "tenants"

TENANTS = [
    "agencia_viajes", "asesor_ai_prod", "clinic", "demo", "ecommerce",
    "escuela_conduccion", "restaurant", "saas", "tienda_ropa",
]


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
    """Copia los archivos de un negocio a un directorio temporal: las pruebas nunca tocan los originales."""
    config_root = tmp_path / "config"
    shutil.copytree(TENANTS_DIR / slug, config_root / "tenants" / slug)
    return ConfigService(base_path=str(config_root))


def run_with_document(monkeypatch, tmp_path: Path, slug: str, mutate: Callable[[dict], object], turns, *, user_id: str = "opciones"):
    """Copia el negocio, modifica su contrato, lo activa como fuente y ejecuta el pipeline real."""
    service = copy_tenant(tmp_path, slug)
    path = BusinessConfigStore(service.tenants_root).path_for(slug)
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    BusinessConfig.model_validate(document)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    monkeypatch.setattr(ai_pipeline_module, "load_tenant_runtime_yaml", functools.partial(load_tenant_runtime_yaml, config_service=service))
    return run_conversation(slug, turns, user_id=user_id)
