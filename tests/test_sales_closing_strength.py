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


TEST_TENANTS = [
    "asesor_ai_prod",
    "restaurant",
    "agencia_viajes",
    "demo",
]


def pushes_next_step(text: str) -> bool:
    normalized = str(text or "").lower()

    strong_signals = [
        "avanz",
        "empez",
        "inici",
        "activar",
        "siguiente paso",
        "continu",
    ]

    outcome_signals = [
        "ya puedes",
        "te permite",
        "dejas de",
        "con esto",
        "así",
    ]

    has_strong = any(s in normalized for s in strong_signals)
    has_outcome = any(s in normalized for s in outcome_signals)

    return has_strong or has_outcome


def is_not_passive(text: str) -> bool:
    normalized = str(text or "").lower()
    passive_patterns = [
        "si tienes alguna duda",
        "puedo ayudarte",
        "avisame",
        "avísame",
        "cuando quieras",
    ]
    return not any(pattern in normalized for pattern in passive_patterns)


def keeps_commercial_tone(text: str) -> bool:
    normalized = str(text or "").lower()
    commercial_signals = [
        "venta",
        "ventas",
        "cliente",
        "negocio",
        "servicio",
        "implement",
        "resultado",
    ]
    return any(signal in normalized for signal in commercial_signals)


def has_followup_invite(text: str) -> bool:
    normalized = str(text or "").lower()
    invite_signals = [
        "dímelo",
        "dimelo",
        "cuéntame",
        "cuentame",
        "te gustaría",
        "te gustaria",
        "profundizar",
    ]
    return any(signal in normalized for signal in invite_signals)


def _tenant(slug: str) -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _ask(message: str, tenant: str):
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml(tenant, channel="whatsapp")

    response, _ai_used, metadata = service.generate_business_reply(
        tenant=_tenant(tenant),
        bot_config=None,
        user_message=message,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=f"closing-{uuid4().hex[:8]}",
        include_metadata=True,
    )

    return str(response or "").lower(), metadata


def test_response_pushes_to_next_step_multi_tenant() -> None:
    for tenant in TEST_TENANTS:
        reply, _metadata = _ask("quiero más información", tenant=tenant)

        assert has_forward_intent(reply) or "?" in reply or pushes_next_step(reply) or has_followup_invite(reply)
        assert keeps_commercial_tone(reply) or len(reply.split()) > 8