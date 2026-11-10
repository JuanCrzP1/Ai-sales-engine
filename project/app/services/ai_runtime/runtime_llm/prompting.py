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

    def __init__(self, prompt_path: str | None = None, message_repository: MessageRepository | None = None) -> None:
        self.settings = settings
        self.provider = settings.llm_provider or "openrouter"
        self.message_repository = message_repository
        self.request_timeout = settings.llm_timeout_seconds
        # Sin clave propia: la plataforma no tiene ninguna. Cada mensaje trae la de su negocio (ver `generate`).
        self.core_ai = CoreAIService(provider=self.provider, request_timeout=self.request_timeout)
        # Solo para pruebas: un cliente ya armado que sustituye la llamada al proveedor.
        self.client = None
        self.prompt_builder = PromptBuilderService(prompt_path=prompt_path)
        self.ai_orchestrator = AIOrchestrator()
        logger.info("ai_service_initialized", extra={"provider": self.provider})

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

    # La respuesta llega en JSON (`app/services/ai/output_contract.py`). Los modelos que no admiten `response_format` lo ignoran
    # y el formato lo sigue pidiendo el prompt.
    RESPONSE_FORMAT = {"type": "json_object"}

    def _call_client(self, client_to_use, *, model_to_use: str, messages: list[dict], temperature: float, max_tokens: int | None, top_p: float | None = None):
        payload = {
            "model": model_to_use,
            "temperature": temperature,
            "messages": messages,
            "response_format": dict(self.RESPONSE_FORMAT),
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        # Un cliente que no acepta un ajuste opcional (los de prueba) recibe la llamada sin él; nunca se llama dos veces al modelo.
        for optional in ("response_format", "top_p", "max_tokens", None):
            try:
                return client_to_use.chat.completions.create(**payload)
            except TypeError:
                if optional is None:
                    raise
                payload.pop(optional, None)

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

    @staticmethod
    def _report_usage(response, *, bot_config, model: str) -> None:
        """Los tokens de esta respuesta, al registro y a quien lleva el consumo del negocio (`MessageAI.on_usage`)."""
        usage = response.get("usage") if isinstance(response, dict) else getattr(response, "usage", None)
        if usage is None:
            return
        usage_dict = usage if isinstance(usage, dict) else vars(usage)
        prompt_tokens = usage_dict.get("prompt_tokens")
        completion_tokens = usage_dict.get("completion_tokens")
        logger.info("tokens_usage", extra={"model": model, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens})
        on_usage = getattr(bot_config, "on_usage", None)
        if callable(on_usage) and isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
            cost = usage_dict.get("cost")
            on_usage(model, prompt_tokens, completion_tokens, float(cost) if isinstance(cost, (int, float)) else None)

    def generate(self, prompt: str, *, user_message: str, bot_config: BotConfig | None = None, history: list[dict] | None = None) -> str:
        """Una llamada al modelo: las instrucciones del negocio, la conversación reciente (`history`) y el mensaje del cliente."""
        if str(os.getenv("LLM_MODE") or "").strip().lower() == "mock_fail":
            raise RuntimeError("mock_fail provider simulation")

        # La clave es la del negocio de este mensaje. El cliente se arma para esta llamada y no se guarda: un mensaje nunca sale
        # con la clave de otro negocio. Sin clave, no hay IA y responde el respaldo del motor.
        business_key = self.core_api_key(getattr(bot_config, "api_key", None))
        client_to_use = self.client or (
            self.core_ai.build_client(provider_override=self.provider, api_key_override=business_key) if business_key else None
        )
        if not client_to_use:
            raise RuntimeError("business_ai_key_missing")

        configured_max_tokens = getattr(bot_config, "max_tokens", None)
        try:
            resolved_max_tokens = int(configured_max_tokens) if configured_max_tokens is not None else 400
        except Exception:
            resolved_max_tokens = 400
        resolved_max_tokens = max(300, min(500, resolved_max_tokens))

        messages = [
            {"role": "system", "content": str(prompt or "")},
            *[{"role": item["role"], "content": item["content"]} for item in (history or []) if item.get("role") in ("user", "assistant")],
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
        self._report_usage(response, bot_config=bot_config, model=str(getattr(bot_config, "model_name", None) or self._default_model()))
        try:
            first_choice = response.choices[0]
        except Exception:
            first_choice = response["choices"][0] if isinstance(response, dict) and response.get("choices") else None
        return str(self._extract_choice_text(first_choice) or "")
