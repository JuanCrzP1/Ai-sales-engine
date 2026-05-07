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
from app.application.pipeline.response_postprocessor import ensure_micro_greeting
from app.application.response_guard import validate_response_against_yaml
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.persistence.memory_repository import MemoryRepository
from app.infrastructure.persistence.subscription_repository import SubscriptionRepository
from app.infrastructure.persistence.usage_repository import UsageRepository
from app.utils.logger import logger


GLOBAL_MEMORY_REPOSITORY = MemoryRepository()
GLOBAL_MEMORY_SERVICE = MemoryDomainService(GLOBAL_MEMORY_REPOSITORY)


def _print_response_audit(response: str, metadata: dict | None) -> None:
    response_text = str(response or "")
    word_count = len(response_text.split())
    char_count = len(response_text)
    lower_text = response_text.lower()

    print(
        {
            "audit_type": "response_metrics",
            "words": word_count,
            "chars": char_count,
            "intent": (metadata or {}).get("intent"),
        }
    )

    dense_signals = 0

    if "precio" in lower_text or "cop" in lower_text:
        dense_signals += 1

    if "te ayuda" in lower_text or "beneficio" in lower_text:
        dense_signals += 1

    if "incluye" in lower_text or "funciona" in lower_text:
        dense_signals += 1

    print(
        {
            "audit_type": "density_signals",
            "score": dense_signals,
        }
    )

    phrases = [
        "responder rápido",
        "no perder ventas",
        "seguimiento",
    ]
    repeat_count = sum(1 for phrase in phrases if phrase in lower_text)

    print(
        {
            "audit_type": "repetition",
            "count": repeat_count,
        }
    )


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

        raw_response = str(response or "")
        conversation_state = str((metadata or {}).get("conversation_state") or "").strip().lower()
        is_first_turn = conversation_state == "new"
        tenant_slug = str((metadata or {}).get("tenant_slug") or getattr(tenant, "slug", "") or "").strip().lower()
        normalized_user_id = str(user_id or "").strip().lower()

        if ai_used and is_first_turn:
            final_response = ensure_micro_greeting(
                raw_response,
                user_message=user_message,
                tenant=tenant_slug,
                user_id=normalized_user_id,
                conversation_state=conversation_state,
            )
        else:
            final_response = raw_response

        response = final_response

        response = validate_response_against_yaml(
            str(response or ""),
            yaml_config if isinstance(yaml_config, dict) else {},
        )
        if str(response or "") != raw_response and ai_used and is_first_turn:
            logger.info(
                {
                    "event": "backend_greeting_postprocess_applied",
                    "tenant": tenant_slug,
                    "user_id": normalized_user_id,
                    "conversation_state": conversation_state,
                }
            )
        _print_response_audit(response, metadata)

        if include_metadata:
            return str(response or ""), bool(ai_used), metadata
        return str(response or ""), bool(ai_used)

    def _mock_business_reply(
        self,
        *,
        tenant,
        bot_config,
        user_message: str,
        faq_results: list[dict],
        yaml_config: dict | None = None,
    ) -> tuple[str, bool]:
        return self.pipeline.run_mock(
            tenant=tenant,
            bot_config=bot_config,
            user_message=user_message,
            faq_results=faq_results,
            yaml_config=yaml_config,
        )
