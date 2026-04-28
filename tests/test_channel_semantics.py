from __future__ import annotations

from app.application.runtime import load_tenant_runtime_yaml
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService


def test_saas_uses_system_channels_not_business() -> None:
    builder = PromptBuilderService()
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")

    capabilities = runtime_yaml.get("capabilities") if isinstance(runtime_yaml.get("capabilities"), dict) else {}
    if not capabilities:
        runtime_yaml["capabilities"] = {}
        capabilities = runtime_yaml["capabilities"]

    capabilities["business_channels"] = {"allowed": []}
    capabilities["system_channels"] = {"allowed": ["whatsapp"]}

    prompt, _metadata, _context = builder.build(
        client_config_id="asesor_ai_prod",
        user_message="como funciona?",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    prompt_text = str(prompt or "").lower()

    assert "canales de atencion (business_channels):" in prompt_text
    assert "sin canales de atencion definidos" in prompt_text
    assert "canales del sistema (system_channels):" in prompt_text
    assert "whatsapp" in prompt_text
    assert "si hablas de como funciona el sistema" in prompt_text
