##### 🧠 SYSTEM OVERVIEW #####
# Sistema SaaS multi-tenant AI-first de ventas conversacionales.
#
# Flujo:
# usuario -> prompt_builder -> IA -> structured_output -> respuesta
#
# La IA es responsable de:
# - entender intención
# - generar respuesta
# - ejecutar venta
#
# El código SOLO:
# - pasa contexto
# - orquesta flujo
#
################################

##### 🚨 AI-FIRST RULE #####
# ❌ PROHIBIDO:
# - lógica comercial en código
# - heurísticas por palabras
# - forzar respuestas
# - if/else por intent
#
# ✅ PERMITIDO:
# - pasar datos
# - estructurar contexto
#
################################

##### ⚠️ ANTI-PATTERNS #####
# NO hacer:
# - if intent == "buy"
# - detectar "quiero"
# - agregar textos manuales de cierre
# - concatenar respuestas
#
# Si haces esto:
# 👉 rompes AI-first
################################
from __future__ import annotations

import os

from app.config import settings
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from app.models import BotConfig, Tenant
from app.repositories.message_repository import MessageRepository
from app.services.ai.ai_orchestrator import AIOrchestrator
from app.services.ai_runtime.runtime_llm.client import AIService as CoreAIService
from app.utils.logger import logger


class RuntimeLLMImplementation:
    STRICT_FALLBACK_MESSAGE = "Se me paso tu mensaje, me cuentas otra vez que necesitas?"

    def __init__(self, prompt_path: str | None = None, bot_config: dict | None = None, message_repository: MessageRepository | None = None) -> None:
        self.settings = settings
        self.provider = settings.llm_provider or "openrouter"
        self.bot_config = bot_config or {}
        provider_token = settings.openrouter_api_key
        if not provider_token and isinstance(self.bot_config, dict):
            provider_token = self.bot_config.get("openrouter_api_key")
        self.provider_api_key = self.core_api_key(provider_token)
        self.message_repository = message_repository
        self.request_timeout = settings.llm_timeout_seconds
        self.core_ai = CoreAIService(provider=self.provider, api_key=self.provider_api_key, request_timeout=self.request_timeout)
        self.client = self.core_ai.client
        self.prompt_builder = PromptBuilderService(prompt_path=prompt_path)
        self.ai_orchestrator = AIOrchestrator()
        logger.info("ai_service_initialized", extra={"provider": self.provider, "api_key_present": bool(self.provider_api_key)})

    @staticmethod
    def core_api_key(value: str | None) -> str:
        token = str(value or "").strip()
        if token in {"", "<<TOKEN>>", "<TOKEN>"}:
            return ""
        return token

    def build_messages(self, client_id: int, limit: int = 10):
        if not self.message_repository:
            return []
        return self.message_repository.list_recent(client_id=client_id, limit=limit)

    def _build_client(self, provider_override: str | None = None, api_key_override: str | None = None):
        self.client = self.core_ai.build_client(provider_override=provider_override, api_key_override=api_key_override)
        return self.client

    def _default_model(self) -> str:
        return self.core_ai.default_model()

    @staticmethod
    def _source_guard_mode() -> str:
        return "disabled"

    @staticmethod
    def _set_runtime_ai_trace(yaml_config: dict | None, trace: dict) -> None:
        if isinstance(yaml_config, dict):
            yaml_config["runtime_ai_trace"] = dict(trace or {})

    @staticmethod
    def validate(text: str | None) -> bool:
        return len(str(text or "").strip()) > 0

    def _call_client(self, client_to_use, *, model_to_use: str, messages: list[dict], temperature: float, max_tokens: int | None, top_p: float | None = None):
        payload = {
            "model": model_to_use,
            "temperature": temperature,
            "messages": messages,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        try:
            return client_to_use.chat.completions.create(**payload)
        except TypeError:
            payload.pop("top_p", None)
            try:
                return client_to_use.chat.completions.create(**payload)
            except TypeError:
                payload.pop("max_tokens", None)
                return client_to_use.chat.completions.create(**payload)

    def _build_prompt(self, *, tenant: Tenant, user_message: str, yaml_config: dict | None = None, faq_results: list[dict] | None = None) -> tuple[str, dict, dict]:
        tenant_slug = str(getattr(tenant, "slug", None) or "").strip() or None
        runtime_yaml = yaml_config if isinstance(yaml_config, dict) else {}
        sales_cfg = runtime_yaml.get("sales") if isinstance(runtime_yaml.get("sales"), dict) else {}
        progression_rules = sales_cfg.get("progression_rules") if isinstance(sales_cfg.get("progression_rules"), dict) else {}

        return self.prompt_builder.build(
            client_config_id=tenant_slug,
            user_message=user_message,
            yaml_config=runtime_yaml,
            faq_results=faq_results,
            progression_rules=progression_rules,
        )

    @staticmethod
    def _extract_choice_text(choice):
        if choice is None:
            return None
        if hasattr(choice, "message") and hasattr(choice.message, "content"):
            return choice.message.content
        if hasattr(choice, "text"):
            return choice.text
        if isinstance(choice, dict):
            message = choice.get("message") or {}
            if isinstance(message, dict) and "content" in message:
                return message.get("content")
            if "text" in choice:
                return choice.get("text")
        return None

    def generate(self, prompt: str, *, user_message: str, bot_config: BotConfig | None = None) -> str:
        if str(os.getenv("LLM_MODE") or "").strip().lower() == "mock_fail":
            raise RuntimeError("mock_fail provider simulation")

        client_to_use = self.client or self._build_client(provider_override=self.provider, api_key_override=self.provider_api_key)
        if not client_to_use:
            raise RuntimeError("LLM client not configured")

        configured_max_tokens = getattr(bot_config, "max_tokens", None)
        try:
            resolved_max_tokens = int(configured_max_tokens) if configured_max_tokens is not None else 400
        except Exception:
            resolved_max_tokens = 400
        resolved_max_tokens = max(300, min(500, resolved_max_tokens))

        messages = [
            {"role": "system", "content": str(prompt or "")},
            {"role": "user", "content": str(user_message or "")},
        ]
        response = self._call_client(
            client_to_use,
            model_to_use=str(getattr(bot_config, "model_name", None) or self._default_model()),
            messages=messages,
            temperature=float(getattr(bot_config, "temperature", None) or 0.6),
            max_tokens=resolved_max_tokens,
            top_p=getattr(bot_config, "top_p", None),
        )
        usage = response.get("usage") if isinstance(response, dict) else getattr(response, "usage", None)
        if usage is not None:
            usage_dict = usage if isinstance(usage, dict) else vars(usage)
            logger.info(
                "tokens_usage",
                extra={
                    "model": str(getattr(bot_config, "model_name", None) or self._default_model()),
                    "prompt_tokens": usage_dict.get("prompt_tokens"),
                    "completion_tokens": usage_dict.get("completion_tokens"),
                    "total_tokens": usage_dict.get("total_tokens"),
                },
            )
        try:
            first_choice = response.choices[0]
        except Exception:
            first_choice = response["choices"][0] if isinstance(response, dict) and response.get("choices") else None
        return str(self._extract_choice_text(first_choice) or "")
