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
from collections.abc import Callable

from app.application.pipeline import AIExecution, ConversationFlow, SalesFlow, log_trace, tenant_slug
from app.application.pipeline.fallback import PLATFORM_FALLBACK_REPLY
from app.application.runtime import BusinessUnavailableError, business_usage_recorder, load_business_ai, load_tenant_runtime_yaml, message_ai
from app.application.runtime.business_ai import UsageCallback
from app.domain.business_config.ai_settings import AICredentials
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.persistence.memory_factory import build_memory_repository
from app.services.ai_runtime.runtime_core import AIService as AIRuntimeService
from app.utils.logger import logger

# Lo que recibe el cliente si no se puede leer la configuración publicada de su negocio: el mensaje neutro de la plataforma (no se
# puede usar el del negocio, que vive en esa configuración). El fallo queda como alerta en el registro (`business_config_unavailable`).
UNAVAILABLE_REPLY = PLATFORM_FALLBACK_REPLY


class AIPipeline:
    def __init__(
        self,
        *,
        prompt_path: str | None = None,
        message_repository=None,
        runtime: AIRuntimeService | None = None,
        memory_service: MemoryDomainService | None = None,
        runtime_loader: Callable[..., dict] | None = None,
        ai_loader: Callable[[str], AICredentials | None] | None = None,
        usage_recorder: Callable[[str], UsageCallback | None] | None = None,
    ) -> None:
        # De dónde salen, en cada mensaje, la configuración del negocio y su IA (su clave de OpenRouter y su modelo). Por defecto,
        # `load_tenant_runtime_yaml` y `load_business_ai`; el área de pruebas del panel pasa la versión que se está probando y la
        # clave de ese negocio. Se resuelven en cada llamada: un mismo motor atiende a muchos negocios y la plataforma no tiene
        # clave propia, así que un mensaje nunca sale con la clave de otro negocio.
        self._runtime_loader = runtime_loader
        self._ai_loader = ai_loader
        # Cada respuesta de la IA suma al consumo de su negocio (lo muestra el panel en «Inteligencia artificial»).
        self._usage_recorder = usage_recorder
        runtime_service = runtime or AIRuntimeService(
            prompt_path=prompt_path,
            message_repository=message_repository,
        )
        if memory_service is None:
            memory_repository = build_memory_repository()
            memory = MemoryDomainService(memory_repository)
        else:
            memory = memory_service
            memory_repository = memory.repository

        self.runtime = runtime_service
        self.memory_repository = memory_repository
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
        load_runtime = self._runtime_loader or load_tenant_runtime_yaml
        try:
            runtime_yaml = load_runtime(
                tenant_slug_value,
                extra_yaml=yaml_config if isinstance(yaml_config, dict) else None,
            )
        except (RuntimeError, ValueError) as exc:
            # `BusinessUnavailableError` ya dejó su alerta; cualquier otro error al armar el runtime también se registra.
            if not isinstance(exc, BusinessUnavailableError):
                logger.error("business_runtime_invalid", extra={"tenant": tenant_slug_value, "error": type(exc).__name__})
            metadata = {"source": "business_unavailable", "intent": "", "tenant_slug": tenant_slug_value}
            if include_metadata:
                return UNAVAILABLE_REPLY, False, metadata
            return UNAVAILABLE_REPLY, False

        # Un mensaje del cliente es un turno de su memoria: se lee una vez al empezar y se guarda una vez al terminar
        # (`infrastructure/persistence/sql_memory.py`).
        memory_key = self.conversation_flow._normalize_user_id(user_id)
        with self.conversation_flow.memory.turn(tenant_slug=tenant_slug_value, user_id=memory_key):
            return self._answer(
                tenant=tenant,
                tenant_slug_value=tenant_slug_value,
                user_id=user_id,
                user_message=user_message,
                bot_config=bot_config,
                conversation_history=conversation_history,
                faq_results=faq_results,
                runtime_yaml=runtime_yaml,
                include_metadata=include_metadata,
            )

    def _answer(
        self,
        *,
        tenant,
        tenant_slug_value: str,
        user_id: str | None,
        user_message: str,
        bot_config,
        conversation_history: list,
        faq_results: list[dict],
        runtime_yaml: dict,
        include_metadata: bool,
    ) -> tuple[str, bool] | tuple[str, bool, dict]:
        """La respuesta a un mensaje, dentro del turno de la memoria del cliente."""
        conversation = self.conversation_flow.process(
            tenant=tenant,
            tenant_slug=tenant_slug_value,
            user_id=user_id,
            user_message=user_message,
            conversation_history=conversation_history,
            runtime_yaml=runtime_yaml,
        )
        if conversation.early_response:
            log_trace(
                tenant_slug_value=tenant_slug_value,
                user_id=conversation.user_id,
                intent="info",
                user_message=user_message,
                final_response=conversation.early_response,
                runtime_yaml=runtime_yaml,
            )
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
        load_ai = self._ai_loader or load_business_ai
        record_usage = (self._usage_recorder or business_usage_recorder)(tenant_slug_value)
        final_response, ai_used, route_context = self.ai_execution.run(
            runtime=self.runtime,
            tenant=tenant,
            bot_config=message_ai(bot_config, load_ai(tenant_slug_value), on_usage=record_usage),
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

        log_trace(
            tenant_slug_value=tenant_slug_value,
            user_id=conversation.user_id,
            intent=route_intent,
            user_message=user_message,
            final_response=str(final_response or ""),
            runtime_yaml=runtime_yaml,
        )
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
