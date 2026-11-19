"""La puerta de entrada de los canales al motor: WhatsApp (QR), Telegram, la API del asistente y «Probar asistente».

Delega todo el turno en `AIPipeline` y entrega la respuesta con los espacios en orden (`tidy_spacing`). Lo que dice el asesor lo
decide la IA: aquí no se infiere la intención ni se cambia una palabra (`services/ai/structured_output.py` es la única fuente de
la intención).
"""
from __future__ import annotations

from app.application.ai_pipeline import AIPipeline
from app.application.pipeline.response_postprocessor import tidy_spacing
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.persistence.memory_factory import build_memory_repository


GLOBAL_MEMORY_REPOSITORY = build_memory_repository()
GLOBAL_MEMORY_SERVICE = MemoryDomainService(GLOBAL_MEMORY_REPOSITORY)


class AIService:
    """Adaptador liviano: delega todo el flujo al AIPipeline."""

    def __init__(self, prompt_path: str | None = None) -> None:
        self.pipeline = AIPipeline(prompt_path=prompt_path, memory_service=GLOBAL_MEMORY_SERVICE)

    def generate_business_reply(
        self,
        tenant,
        bot_config,
        user_message: str,
        conversation_history: list,
        faq_results: list[dict],
        yaml_config: dict | None = None,
        user_id: str | None = None,
        include_metadata: bool = False,
    ) -> tuple[str, bool] | tuple[str, bool, dict]:
        incoming_memory = yaml_config.get("memory_context") if isinstance(yaml_config, dict) else None

        result = self.pipeline.run(
            tenant=tenant,
            user_message=user_message,
            user_id=user_id,
            bot_config=bot_config,
            conversation_history=conversation_history,
            faq_results=faq_results,
            yaml_config=yaml_config,
            include_metadata=include_metadata,
        )

        if isinstance(result, tuple) and len(result) == 3:
            response, ai_used, metadata = result
            metadata = metadata if isinstance(metadata, dict) else {}
        else:
            response, ai_used = result
            metadata = {}

        if not isinstance(metadata.get("memory_context"), dict):
            metadata["memory_context"] = {}
        if isinstance(incoming_memory, dict) and incoming_memory:
            metadata["memory_context"] = {**incoming_memory, **metadata["memory_context"]}

        response = tidy_spacing(response)
        if include_metadata:
            return response, bool(ai_used), metadata
        return response, bool(ai_used)
