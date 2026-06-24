##### 🚨 PIPELINE CONTROL — NO DECISION LOGIC #####
# Este módulo valida flujo, NO decide negocio.
#
# ❌ PROHIBIDO:
# - clasificar intent
# - usar heurísticas
# - cambiar respuesta
#
# SOLO:
# - validar estado
# - enrutar flujo
#
# Si algo falla:
# → NO inventar lógica
################################

##### ⚠️ MULTI-TENANT #####
# Esto es MULTI-TENANT.
#
# NO escribir nada específico de un negocio.
# NO mencionar productos.
# NO hardcodear comportamiento.
#
# Esto debe funcionar para cualquier YAML.
################################

##### 🧠 AI-FIRST ENFORCEMENT #####
# La IA es la única que decide:
#
# - intent
# - respuesta
# - flujo de conversación
#
# ❌ PROHIBIDO en código:
# - clasificar intent
# - usar heurísticas
# - usar if/else por intención
# - modificar respuestas manualmente
#
# ✅ El código SOLO:
# - pasa contexto
# - orquesta flujo
# - valida estado
#
# Si algo falla:
# → se corrige el prompt
# → NO el código
################################

from __future__ import annotations

import copy

from app.application.pipeline import AIExecution, ConversationFlow, SaaSGuard, SalesFlow, blocked_response, log_trace, service_unavailable_response, tenant_key, tenant_slug
from app.application.runtime import load_tenant_runtime_yaml
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.persistence.memory_repository import MemoryRepository, SQLMemoryRepository
from app.infrastructure.persistence.subscription_repository import SubscriptionRepository
from app.infrastructure.persistence.usage_repository import UsageRepository
from app.services.ai_runtime.runtime_core import AIService as AIRuntimeService
from app.utils.logger import logger


class AIPipeline:
    def __init__(
        self,
        *,
        prompt_path: str | None = None,
        bot_config: dict | None = None,
        message_repository=None,
        runtime: AIRuntimeService | None = None,
        memory_service: MemoryDomainService | None = None,
        subscription_repo: SubscriptionRepository,
        usage_repo: UsageRepository,
    ) -> None:
        runtime_service = runtime or AIRuntimeService(
            prompt_path=prompt_path,
            bot_config=bot_config,
            message_repository=message_repository,
        )
        if memory_service is None:
            memory_repository = SQLMemoryRepository()
            memory = MemoryDomainService(memory_repository)
        else:
            memory = memory_service
            memory_repository = memory.repository

        self.runtime = runtime_service
        self.usage_repo = usage_repo
        self.memory_repository = memory_repository
        self.saas_guard = SaaSGuard(subscription_repo=subscription_repo, usage_repo=usage_repo)
        self.conversation_flow = ConversationFlow(memory_service=memory)
        self.sales_flow = SalesFlow()
        self.ai_execution = AIExecution()

    def run(
        self,
        *,
        tenant,
        user_message: str,
        user_id: str | None,
        bot_config,
        conversation_history: list,
        faq_results: list[dict],
        yaml_config: dict | None,
        include_metadata: bool = False,
    ) -> tuple[str, bool] | tuple[str, bool, dict]:
        tenant_slug_value = tenant_slug(tenant)
        try:
            runtime_yaml = load_tenant_runtime_yaml(
                tenant_slug_value,
                extra_yaml=yaml_config if isinstance(yaml_config, dict) else None,
            )
        except (RuntimeError, ValueError) as exc:
            runtime_error_response = "Error de configuración de tenant: runtime_yaml inválido."
            metadata = {
                "source": "runtime_yaml_invalid",
                "intent": "info",
                "tenant_slug": tenant_slug_value,
                "error": str(exc),
            }
            if include_metadata:
                return runtime_error_response, False, metadata
            return runtime_error_response, False
        tenant_key_value = tenant_key(tenant)

        try:
            allowed, reason = self.saas_guard.check_access(tenant_key_value)
        except Exception as exc:
            # Resiliencia: una falla de dependencia crítica (ej. PostgreSQL caído)
            # NO debe propagar un traceback al usuario. Respuesta controlada + log.
            logger.error(
                "saas_guard_unavailable",
                extra={"tenant": tenant_slug_value, "error": str(exc)},
            )
            controlled = service_unavailable_response()
            log_trace(tenant_slug_value=tenant_slug_value, user_id=str(user_id or "anonymous"), intent="info", user_message=user_message, final_response=controlled)
            metadata = {
                "source": "saas_guard_unavailable",
                "intent": "info",
                "tenant_slug": tenant_slug_value,
            }
            if include_metadata:
                return controlled, False, metadata
            return controlled, False
        if not allowed:
            blocked = blocked_response(reason)
            log_trace(tenant_slug_value=tenant_slug_value, user_id=str(user_id or "anonymous"), intent="info", user_message=user_message, final_response=blocked)
            metadata = {
                "source": "saas_guard_blocked",
                "intent": "info",
                "tenant_slug": tenant_slug_value,
            }
            if include_metadata:
                return blocked, False, metadata
            return blocked, False

        conversation = self.conversation_flow.process(
            tenant=tenant,
            tenant_slug=tenant_slug_value,
            user_id=user_id,
            user_message=user_message,
            conversation_history=conversation_history,
            runtime_yaml=runtime_yaml,
        )
        if conversation.early_response:
            log_trace(tenant_slug_value=tenant_slug_value, user_id=conversation.user_id, intent="info", user_message=user_message, final_response=conversation.early_response)
            metadata = {
                "source": str(conversation.early_source or "early_response"),
                "intent": "info",
                "tenant_slug": tenant_slug_value,
            }
            if include_metadata:
                return conversation.early_response, False, metadata
            return conversation.early_response, False

        self.sales_flow.build(
            tenant_slug=tenant_slug_value,
            user_message=user_message,
            runtime_yaml=conversation.runtime_yaml,
        )
        runtime_yaml_for_ai = copy.deepcopy(conversation.runtime_yaml)
        logger.info("runtime_yaml_valid", extra={
            "tenant": tenant_slug_value,
            "has_pricing": bool(runtime_yaml_for_ai.get("pricing")),
            "has_business": bool(runtime_yaml_for_ai.get("business")),
        })
        final_response, ai_used, route_context = self.ai_execution.run(
            runtime=self.runtime,
            tenant=tenant,
            bot_config=bot_config,
            user_message=user_message,
            conversation_history=conversation_history,
            faq_results=faq_results,
            runtime_yaml=runtime_yaml_for_ai,
            memory_service=self.conversation_flow.memory,
            tenant_slug=tenant_slug_value,
            user_id=conversation.user_id,
        )
        route_context = route_context if isinstance(route_context, dict) else {}
        route_intent = str(route_context.get("intent") or "").strip().lower()

        # Registrar consumo SOLO cuando la IA produjo una respuesta válida.
        # Excluye saludos/demo/bloqueos (early-return) y fallbacks (ai_used=False).
        # Protegido para que un fallo de DB en el incremento no pierda la respuesta.
        if ai_used and str(final_response or "").strip():
            try:
                self.saas_guard.record_usage(tenant_key_value)
            except Exception as exc:
                logger.error(
                    "usage_record_failed",
                    extra={"tenant": tenant_slug_value, "error": str(exc)},
                )

        log_trace(tenant_slug_value=tenant_slug_value, user_id=conversation.user_id, intent=route_intent, user_message=user_message, final_response=str(final_response or ""))
        if include_metadata:
            metadata = route_context if isinstance(route_context, dict) else {}
            if "source" not in metadata:
                metadata = {**metadata, "source": "unknown"}
            if "tenant_slug" not in metadata:
                metadata = {**metadata, "tenant_slug": tenant_slug_value}
            return final_response, ai_used, metadata
        return final_response, ai_used

    def run_mock(self, *, tenant, bot_config, user_message: str, faq_results: list[dict], yaml_config: dict | None) -> tuple[str, bool]:
        return self.run(
            tenant=tenant,
            user_message=user_message,
            user_id="mock-user",
            bot_config=bot_config,
            conversation_history=[],
            faq_results=faq_results,
            yaml_config=yaml_config,
            include_metadata=False,
        )
