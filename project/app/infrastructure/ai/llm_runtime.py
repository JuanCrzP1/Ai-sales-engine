"""La llamada al modelo de cada mensaje, con la clave y el modelo del negocio (`LLMRuntime`).

`generate` arma la conversación (las instrucciones del negocio, lo reciente del chat y el mensaje del cliente) y `classify` hace una
llamada corta y exacta para entender un mensaje (el lector de pagos). Las dos usan el cliente de OpenRouter (`openrouter_client.py`)
con la clave del negocio de ese mensaje, que nunca se guarda, y registran los tokens para el consumo del negocio.

AI-first: aquí no se decide nada del mensaje ni de la venta; solo se pasa el contexto y se devuelve lo que respondió el modelo.
Antes vivía en `services/ai_runtime/` repartida en tres clases que solo se heredaban entre sí (retirado el 19 de noviembre de 2026).
"""
from __future__ import annotations

import os

from app.config import settings
from app.infrastructure.ai.ai_orchestrator import AIOrchestrator
from app.infrastructure.ai.openrouter_client import OpenRouterClient
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from app.utils.logger import logger


class LLMRuntime:
    def __init__(self, prompt_path: str | None = None) -> None:
        self.settings = settings
        self.provider = settings.llm_provider or "openrouter"
        self.request_timeout = settings.llm_timeout_seconds
        # Sin clave propia: la plataforma no tiene ninguna. Cada mensaje trae la de su negocio (ver `generate`).
        self.core_ai = OpenRouterClient(provider=self.provider, request_timeout=self.request_timeout)
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

    # La respuesta llega en JSON (`app/infrastructure/ai/prompting/output_contract.py`). Los modelos que no admiten `response_format` lo ignoran
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

    def _build_prompt(self, *, tenant, user_message: str, yaml_config: dict | None = None, faq_results: list[dict] | None = None) -> tuple[str, dict, dict]:
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

    def generate(self, prompt: str, *, user_message: str, bot_config: object | None = None, history: list[dict] | None = None) -> str:
        """Una llamada al modelo: las instrucciones del negocio, la conversación reciente (`history`) y el mensaje del cliente."""
        configured_max_tokens = getattr(bot_config, "max_tokens", None)
        try:
            resolved_max_tokens = int(configured_max_tokens) if configured_max_tokens is not None else 400
        except Exception:
            resolved_max_tokens = 400
        messages = [
            {"role": "system", "content": str(prompt or "")},
            *[{"role": item["role"], "content": item["content"]} for item in (history or []) if item.get("role") in ("user", "assistant")],
            {"role": "user", "content": str(user_message or "")},
        ]
        return self._complete(
            messages,
            bot_config=bot_config,
            temperature=float(getattr(bot_config, "temperature", None) or 0.6),
            max_tokens=max(300, min(500, resolved_max_tokens)),
            top_p=getattr(bot_config, "top_p", None),
        )

    def classify(self, prompt: str, *, user_message: str, bot_config: object | None = None, max_tokens: int = 120) -> str:
        """Una llamada corta y exacta (sin creatividad) para entender un mensaje, con la clave y el modelo del negocio. La usa el
        lector de pagos (`application/pipeline/payment_reading.py`); también responde en JSON."""
        messages = [{"role": "system", "content": str(prompt or "")}, {"role": "user", "content": str(user_message or "")}]
        return self._complete(messages, bot_config=bot_config, temperature=0.0, max_tokens=max_tokens)

    def _complete(self, messages: list[dict], *, bot_config: object | None, temperature: float, max_tokens: int, top_p: float | None = None) -> str:
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

        model = str(getattr(bot_config, "model_name", None) or self._default_model())
        response = self._call_client(client_to_use, model_to_use=model, messages=messages, temperature=temperature, max_tokens=max_tokens, top_p=top_p)
        self._report_usage(response, bot_config=bot_config, model=model)
        try:
            first_choice = response.choices[0]
        except Exception:
            first_choice = response["choices"][0] if isinstance(response, dict) and response.get("choices") else None
        return str(self._extract_choice_text(first_choice) or "")
