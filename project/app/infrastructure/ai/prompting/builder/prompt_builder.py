"""Entrada pública del prompt: valida el runtime del mensaje y delega en el compositor (`prompting/composer.py`).

Cada parte del prompt vive en su bloque (`prompting/sections/`) y las instrucciones fijas de la plataforma en
`prompting/instructions.py`. Esta clase no arma texto.
"""
from __future__ import annotations

from app.domain.ai.prompt_context import build_prompt_context
from app.infrastructure.ai.prompting.composer import compose
from app.infrastructure.ai.prompting.view import PromptView, validate_runtime_yaml

PROMPT_METADATA = {
    "prompt_path": "",
    "prompt_text": "",
    "prompt_hash": "",
    "prompt_version": "single-source-v1",
    "prompt_source": "single_contract_blocks",
}


class PromptBuilderService:
    def __init__(self, *, prompt_path: str | None = None) -> None:
        del prompt_path

    def build(
        self,
        *,
        client_config_id: str | None,
        user_message: str,
        yaml_config: dict | None,
        faq_results: list[dict] | None,
        progression_rules: dict | None,
        **_kwargs,
    ) -> tuple[str, dict, dict]:
        """El prompt del mensaje, sus metadatos y el contexto mínimo de la conversación."""
        del progression_rules, faq_results
        from app.application.runtime.runtime_yaml_builder import RuntimeYamlBuilder

        slug = str(client_config_id or "").strip()
        runtime = dict(RuntimeYamlBuilder().build(tenant_slug=slug, partial_yaml=yaml_config if isinstance(yaml_config, dict) else {}))
        validate_runtime_yaml(runtime)
        runtime.setdefault("tenant_slug", slug.lower())
        memory = runtime.get("memory_context") if isinstance(runtime.get("memory_context"), dict) else {}
        context = build_prompt_context(user_message=user_message, yaml_config=runtime, memory=memory)
        return compose(PromptView(runtime, user_message)), dict(PROMPT_METADATA), context
