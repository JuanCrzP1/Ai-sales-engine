from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.application.runtime import load_tenant_runtime_yaml
from app.services.ai_service import AIService

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def _tenant(slug: str = "asesor_ai_prod") -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _ask_with_prime(*, runtime_yaml: dict, user_message: str, user_id: str) -> str:
    service = AIService()

    # Evita que el mensaje inicial automatico contamine el assert del turno bajo prueba.
    service.generate_business_reply(
        tenant=_tenant("asesor_ai_prod"),
        bot_config=None,
        user_message="hola",
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=user_id,
        include_metadata=True,
    )

    response, _ai_used, _metadata = service.generate_business_reply(
        tenant=_tenant("asesor_ai_prod"),
        bot_config=None,
        user_message=user_message,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=user_id,
        include_metadata=True,
    )

    return str(response or "").lower()


def test_response_does_not_invent_channels() -> None:
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
    capabilities = runtime_yaml.get("capabilities") if isinstance(runtime_yaml.get("capabilities"), dict) else {}
    runtime_yaml["capabilities"] = capabilities

    capabilities["system_channels"] = {"allowed": ["whatsapp"]}
    capabilities["business_channels"] = {"allowed": []}

    text = _ask_with_prime(
        runtime_yaml=runtime_yaml,
        user_message="solo funciona por whatsapp?",
        user_id=f"test-no-invent-{uuid4().hex[:8]}",
    )

    assert "whatsapp" in text
    assert "instagram" not in text
    assert "web" not in text


def test_single_channel_is_positioned_as_main() -> None:
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
    capabilities = runtime_yaml.get("capabilities") if isinstance(runtime_yaml.get("capabilities"), dict) else {}
    runtime_yaml["capabilities"] = capabilities

    capabilities["system_channels"] = {"allowed": ["whatsapp"]}
    capabilities["business_channels"] = {"allowed": []}

    text = _ask_with_prime(
        runtime_yaml=runtime_yaml,
        user_message="como funciona?",
        user_id=f"test-main-channel-{uuid4().hex[:8]}",
    )

    assert "instagram" not in text
    assert "web" not in text


def test_multiple_channels_are_respected() -> None:
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
    capabilities = runtime_yaml.get("capabilities") if isinstance(runtime_yaml.get("capabilities"), dict) else {}
    runtime_yaml["capabilities"] = capabilities

    capabilities["business_channels"] = {"allowed": []}
    capabilities["system_channels"] = {"allowed": ["whatsapp", "instagram"]}

    text = _ask_with_prime(
        runtime_yaml=runtime_yaml,
        user_message="por donde atienden?",
        user_id=f"test-multi-channel-{uuid4().hex[:8]}",
    )

    assert "web" not in text
