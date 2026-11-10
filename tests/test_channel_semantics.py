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

    # Lo que vende funciona por WhatsApp (canal del producto); el negocio no declaró por dónde atiende: no se inventa uno.
    assert "lo que vende funciona en: whatsapp." in prompt_text
    assert "atiendes por:" not in prompt_text
