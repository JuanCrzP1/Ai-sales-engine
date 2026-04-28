## ========================================
## ARCHIVO: test_sales_pressure.py
##
## QUÉ VALIDA:
## Que ante un dolor real el bot mencione el problema, conecte con impacto
## y empuje un siguiente paso concreto.
##
## POR QUÉ ES CRÍTICO:
## Un bot que solo responde pero no avanza no convierte.
##
## QUÉ PROTEGE:
## Presión comercial activa en respuesta a pain real del usuario.
## ========================================

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.runtime import load_tenant_runtime_yaml
from app.services.ai_service import AIService
from semantic_guard import has_forward_intent


def _tenant(slug: str = "asesor_ai_prod") -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _ask_pain(message: str) -> str:
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")
    response, _ai_used, _metadata = service.generate_business_reply(
        tenant=_tenant(),
        bot_config=None,
        user_message=message,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=f"pressure-{uuid4().hex[:8]}",
        include_metadata=True,
    )
    return str(response or "").lower()


def _has_any_signal(text: str, signals: list[str]) -> bool:
    normalized = str(text or "").lower()
    return any(signal in normalized for signal in signals)


def _mentions_real_problem(text: str) -> bool:
    return _has_any_signal(
        text,
        ["mensaj", "respuest", "respond", "atend", "client", "volum", "alcan", "recib", "seguim", "carga", "satur", "desbord"],
    )


def _shows_commercial_impact(text: str) -> bool:
    normalized = str(text or "").lower()
    impact_groups = [
        ["vent", "negoci", "result", "oportun", "convers"],
        ["perd", "demor", "enfri", "cae", "desorden", "cuello", "satur", "carga", "escala", "tiempo"],
        ["seguim", "respuest", "respond", "client", "orden"],
    ]
    matched_groups = sum(1 for group in impact_groups if any(signal in normalized for signal in group))
    return matched_groups >= 2


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Valida que ante "tengo muchos mensajes" el bot reconozca el problema real.
##
## POR QUÉ ES IMPORTANTE:
## Un bot que ignora el dolor expresado no conecta ni vende.
##
## QUÉ PROTEGE:
## Reconocimiento de pain y conexión con contexto de negocio.
## ----------------------------------------
def test_sales_pressure_mentions_real_problem() -> None:
    reply = _ask_pain("tengo muchos mensajes")

    ## Debe mencionar el problema (mensajes, respuestas, atención, clientes, volumen)
    assert _mentions_real_problem(reply), f"La respuesta no menciona el problema real: {reply!r}"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Valida que la respuesta conecte con impacto comercial.
##
## POR QUÉ ES IMPORTANTE:
## Conectar dolor con impacto crea urgencia y avance hacia decisión.
##
## QUÉ PROTEGE:
## Narrativa de impacto en respuesta a pain real.
## ----------------------------------------
def test_sales_pressure_connects_with_impact() -> None:
    reply = _ask_pain("tengo muchos mensajes")

    ## Debe conectar problema con consecuencia o impacto comercial,
    ## sin depender de una sola palabra exacta del modelo.
    assert _shows_commercial_impact(reply), f"La respuesta no conecta con impacto comercial: {reply!r}"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Valida que la respuesta empuje un siguiente paso concreto.
##
## POR QUÉ ES IMPORTANTE:
## Sin siguiente paso la conversación muere, no convierte.
##
## QUÉ PROTEGE:
## Avance hacia decisión en cada turno comercial.
## ----------------------------------------
def test_sales_pressure_pushes_next_step() -> None:
    reply = _ask_pain("tengo muchos mensajes")

    ## Debe empujar: pregunta, acción, propuesta
    assert "?" in reply or has_forward_intent(reply), (
        f"La respuesta no empuja siguiente paso: {reply!r}"
    )
