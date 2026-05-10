##### 🚨 AI-FIRST ARCHITECTURE RULE #####
# Este sistema es AI-first.
#
# ❌ PROHIBIDO:
# - NO inferir intent fuera de structured_output.py
# - NO usar heurísticas ("quiero", "comprar", etc.)
# - NO crear lógica comercial en código
# - NO forzar respuestas
# - NO agregar reglas de cierre
#
# ✅ PERMITIDO:
# - pasar contexto
# - estructurar datos
# - delegar completamente en la IA
#
# 💣 SI VIOLAS ESTO:
# rompes consistencia, ventas y multi-tenant
#########################################
##### 🚫 NO INTENT MANIPULATION #####
# Este servicio NO puede tocar intent.
#
# ❌ NO:
# - sobrescribir metadata.intent
# - ajustar intent
################################
from __future__ import annotations

from app.application.ai_pipeline import AIPipeline
from app.application.response_guard import validate_response_against_yaml
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.persistence.memory_repository import MemoryRepository, SQLMemoryRepository
from app.infrastructure.persistence.subscription_repository import SubscriptionRepository
from app.infrastructure.persistence.usage_repository import UsageRepository
from app.utils.logger import logger


GLOBAL_MEMORY_REPOSITORY = SQLMemoryRepository()
GLOBAL_MEMORY_SERVICE = MemoryDomainService(GLOBAL_MEMORY_REPOSITORY)


def _extract_price_anchor(text: str, runtime_yaml: dict) -> str:
    pricing = runtime_yaml.get("pricing", {})
    plans = pricing.get("plans", [])
    if not plans:
        return ""

    p = plans[0]
    monthly = str(p.get("pricing", {}).get("COP", {}).get("monthly") or "")
    implementation = str(p.get("pricing", {}).get("COP", {}).get("implementation") or "")

    text_lower = str(text or "").lower()

    if monthly and monthly in text_lower:
        return f"mensual {monthly}"

    if implementation and implementation in text_lower:
        return f"implementación {implementation}"

    return ""


# 🚨 ARCHITECTURE RULE:
# Este modulo NO puede modificar, inferir ni ajustar el intent.
# structured_output.py es la unica fuente de intent.
# Cualquier cambio aqui rompe la consistencia del sistema.
#
# ⚠️ NO HACER:
# - NO recalcular intent
# - NO sobrescribir metadata.intent
# - NO inferir comportamiento comercial


class AIService:
    """Adapter liviano: delega todo el flujo al AIPipeline."""

    def __init__(self, prompt_path: str | None = None, bot_config: dict | None = None, message_repository=None) -> None:
        subscription_repo = SubscriptionRepository()
        usage_repo = UsageRepository()
        self.pipeline = AIPipeline(
            prompt_path=prompt_path,
            bot_config=bot_config,
            message_repository=message_repository,
            memory_service=GLOBAL_MEMORY_SERVICE,
            subscription_repo=subscription_repo,
            usage_repo=usage_repo,
        )

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
        if isinstance(yaml_config, dict):
            incoming_memory = yaml_config.get("memory_context")
        else:
            incoming_memory = None

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
            safe_metadata = metadata if isinstance(metadata, dict) else {}
        else:
            response, ai_used = result
            safe_metadata = {}

        metadata = safe_metadata

        if not isinstance(metadata.get("memory_context"), dict):
            metadata["memory_context"] = {}

        if incoming_memory and isinstance(incoming_memory, dict):
            metadata_memory = metadata.get("memory_context") or {}
            metadata_memory = {**incoming_memory, **metadata_memory}
            metadata["memory_context"] = metadata_memory

        price_anchor = _extract_price_anchor(response, yaml_config if isinstance(yaml_config, dict) else {})

        if price_anchor:
            if isinstance(metadata, dict):
                memory = metadata.get("memory_context") or {}
                memory["price_anchor"] = price_anchor
                metadata["memory_context"] = memory

        response = validate_response_against_yaml(
            str(response or ""),
            yaml_config if isinstance(yaml_config, dict) else {},
        )

        if include_metadata:
            return str(response or ""), bool(ai_used), metadata
        return str(response or ""), bool(ai_used)
