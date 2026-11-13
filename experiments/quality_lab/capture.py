"""Corre dentro de una copia aislada del código (sin `.env`): conversa con el modelo real los escenarios de cada negocio.

Arma su almacén temporal con los negocios de ejemplo (importados de sus YAML), les guarda la clave de IA del laboratorio y bloquea
toda la red salvo OpenRouter. Registra cada respuesta, el prompt que salió y los tokens. Los datos de pago reales que entrega el motor
se reemplazan por un marcador antes de escribir el resultado.

    python capture.py <ajustes.json>
"""
from __future__ import annotations

import json
import logging
import os
import socket
import sys
import time
from pathlib import Path
from types import SimpleNamespace

TREE = Path(__file__).resolve().parents[2]
PROJECT = TREE / "project"
ALLOWED_HOSTS = {"openrouter.ai"}


def _guard_network() -> list[str]:
    attempts: list[str] = []
    allowed = {"127.0.0.1", "::1", "localhost"}
    real_lookup, real_connect = socket.getaddrinfo, socket.socket.connect

    def lookup(host, *args, **kwargs):
        name = host.decode() if isinstance(host, bytes) else str(host)
        if name in allowed or name in ALLOWED_HOSTS:
            found = real_lookup(host, *args, **kwargs)
            allowed.update(item[4][0] for item in found)
            return found
        attempts.append(name)
        raise OSError("red bloqueada por el laboratorio")

    def connect(self, address):
        host = str(address[0]) if isinstance(address, tuple) else "socket"
        if host in allowed:
            return real_connect(self, address)
        attempts.append(host)
        raise OSError("red bloqueada por el laboratorio")

    socket.getaddrinfo, socket.socket.connect = lookup, connect
    return attempts


def _prepare_store(api_key: str) -> list[str]:
    from cryptography.fernet import Fernet

    path = TREE / ".almacen-calidad" / "negocios.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    os.environ["BUSINESS_CONFIG_DATABASE_URL"] = f"sqlite:///{path.as_posix()}"
    os.environ["BUSINESS_CONFIG_SECRETS_KEY"] = Fernet.generate_key().decode()
    from app.infrastructure.business_config.ai_settings_store import AISettingsStore
    from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
    try:
        from app.infrastructure.business_config.example_businesses import import_examples as importer
    except ImportError:
        # Una copia anterior al 11 de noviembre de 2026 importa los ejemplos de sus YAML.
        from app.infrastructure.config.config_service import ConfigService
        from app.infrastructure.config.legacy_store_migration import import_all

        def importer(service):
            return import_all(service, ConfigService())

    engine = create_business_config_engine(os.environ["BUSINESS_CONFIG_DATABASE_URL"])
    create_local_schema(engine)
    report = importer(build_business_config_service(engine, secrets_key=os.environ["BUSINESS_CONFIG_SECRETS_KEY"]))
    keys = AISettingsStore(engine, os.environ["BUSINESS_CONFIG_SECRETS_KEY"])
    for slug in report.created:
        keys.save_ai_settings(slug, model=None, api_key=api_key, clear_key=False)
    engine.dispose()
    return sorted(report.created)


def _converse(service, slug: str, customer: str, name: str, script: list[dict], calls: list[dict], secrets: list[str]) -> list[dict]:
    """Una conversación completa de un cliente con el asesor: cada turno con su respuesta (sin datos de pago), lo que decidió el motor
    y las llamadas al modelo que costó."""
    from app.application.runtime import load_tenant_runtime_yaml

    tenant = SimpleNamespace(slug=slug, name=slug, id=slug)
    turns = []
    for step in script:
        calls.clear()
        reply, ai_used, metadata = service.generate_business_reply(
            tenant=tenant, bot_config=None, user_message=step["message"], conversation_history=[], faq_results=[],
            yaml_config=load_tenant_runtime_yaml(slug, channel="whatsapp"), user_id=customer, include_metadata=True,
        )
        metadata = metadata if isinstance(metadata, dict) else {}
        ai_metadata = metadata.get("ai_metadata") if isinstance(metadata.get("ai_metadata"), dict) else {}
        shown = str(reply or "")
        delivered = any(secret in shown for secret in secrets)
        for secret in secrets:
            shown = shown.replace(secret, "[dato entregado por el motor]")
        turns.append({
            **step, "conversation": name, "reply": shown, "engine_delivered_payment": delivered, "ai_used": bool(ai_used),
            "handoff": bool(metadata.get("handoff")),
            "intent": metadata.get("intent"), "source": metadata.get("source"), "format_error": str(ai_metadata.get("format_error") or ""),
            "calls": [{key: value for key, value in call.items() if key != "system"} for call in calls],
            "system_prompt": calls[-1]["system"] if calls else "",
        })
    return turns


def main(settings_path: str) -> int:
    settings = json.loads(Path(settings_path).read_text(encoding="utf-8"))
    if (TREE / ".env").exists() or (PROJECT / ".env").exists():
        raise SystemExit("Se detiene: la copia tiene .env.")
    attempts = _guard_network()
    logging.disable(logging.CRITICAL)
    sys.path[:0] = [str(PROJECT), str(Path(__file__).resolve().parent)]
    slugs = _prepare_store(os.environ["OPENROUTER_API_KEY"])

    import requests

    from facts import business_facts
    from scenarios import turns_for
    from standard import conversations_for

    calls: list[dict] = []
    real_post = requests.post

    def recording_post(url, headers=None, json=None, timeout=None, **kwargs):  # noqa: A002 - misma firma que requests.post
        started = time.monotonic()
        response = real_post(url, headers=headers, json=json, timeout=timeout, **kwargs)
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        system = next((m.get("content") or "" for m in (json or {}).get("messages", []) if m.get("role") == "system"), "")
        calls.append({"status": response.status_code, "ms": int((time.monotonic() - started) * 1000), "usage": body.get("usage") or {},
                      "system_chars": len(system), "messages": len((json or {}).get("messages", [])), "system": system})
        return response

    requests.post = recording_post

    from app.application.runtime import load_tenant_runtime_yaml
    from app.domain.business_config.payment_data import payment_values
    from app.infrastructure.ai.prompting.business_model import detect_business_model
    from app.services.ai_service import AIService

    service = AIService()
    wanted = settings.get("tenants") or slugs
    results: dict[str, dict] = {}
    for slug in wanted:
        runtime = load_tenant_runtime_yaml(slug, channel="whatsapp")
        facts = business_facts(runtime, detect_business_model(runtime))
        secrets = sorted(payment_values(runtime), key=len, reverse=True)
        samples = []
        for sample in range(int(settings.get("samples", 1))):
            # El guion del negocio (una conversación por muestra) o, con `standard`, las conversaciones del estándar del asesor: cada
            # una es un cliente distinto y queda como una muestra más.
            scripts = conversations_for(facts) if settings.get("standard") else [("guion", turns_for(facts))]
            for position, (name, script) in enumerate(scripts):
                customer = f"calidad-{slug}-{sample}" + (f"-{position}" if settings.get("standard") else "")
                samples.append(_converse(service, slug, customer, name, script, calls, secrets))
        results[slug] = {"facts": facts, "samples": samples}

    Path(settings["output"]).write_text(json.dumps({"label": settings["label"], "commit": settings["commit"], "model": os.environ.get("OPENROUTER_MODEL"),
                                                    "results": results, "network_attempts": attempts}, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
