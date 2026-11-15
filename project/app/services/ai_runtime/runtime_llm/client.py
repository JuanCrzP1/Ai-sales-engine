from __future__ import annotations

import logging
import time

import requests

from app.config import settings
from app.utils.logger import logger


def _error_code(response) -> str:
    """El código del error que devolvió OpenRouter, sin su mensaje: puede repetir parte de lo enviado."""
    try:
        error = response.json().get('error') or {}
    except ValueError:
        return ''
    return str(error.get('code') or '') if isinstance(error, dict) else ''


# El asesor conversa por chat y cada respuesta tiene un tope de tokens. Un modelo que razona antes de responder gastaba ese tope
# pensando y no le quedaba para escribir: el cliente recibía «Hubo un problema…» (Claude Haiku 5.5 en 25 de 32 mensajes y GPT-6 Luna en
# 12, puerta de calidad del 14 nov 2026, `modelo_r1_*`). Sin razonar responde completo, más rápido y más barato. Los modelos que no
# razonan aceptan el ajuste y no cambian.
NO_REASONING = {'enabled': False}
# Algunos modelos siempre razonan y rechazan apagarlo (gpt-5-mini, gemini-2.5-pro: «Reasoning is mandatory…»). Con ellos, lo mínimo.
LEAST_REASONING = {'effort': 'minimal'}
# Los modelos que ya lo rechazaron en este proceso: con ellos se pide lo mínimo desde la primera llamada.
_MANDATORY_REASONING: set[str] = set()


def _reasoning_is_mandatory(response) -> bool:
    """Si OpenRouter rechazó la llamada porque ese modelo no puede dejar de razonar."""
    if response.status_code != 400:
        return False
    try:
        error = response.json().get('error') or {}
    except ValueError:
        return False
    message = str(error.get('message') or '') if isinstance(error, dict) else ''
    return 'reasoning is mandatory' in message.lower()


class _OpenRouterCompletions:
    def __init__(self, api_key: str, base_url: str, timeout: int, max_retries: int):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries

    class Chat:
        def __init__(self, parent):
            self._parent = parent

        class _Completions:
            def __init__(self, parent):
                self._parent = parent

            def create(self, model, temperature=None, messages=None, **kwargs):
                base = self._parent._parent.base_url.rstrip('/')
                url = f'{base}/chat/completions' if base.endswith('/v1') else f'{base}/v1/chat/completions'
                headers = {
                    'Authorization': f'Bearer {self._parent._parent.api_key}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': settings.public_base_url,
                    'X-Title': settings.app_name,
                }
                payload = {'model': model}
                if messages is not None:
                    payload['messages'] = messages
                if temperature is not None:
                    payload['temperature'] = temperature
                payload.update(kwargs or {})
                payload.setdefault('reasoning', dict(LEAST_REASONING if model in _MANDATORY_REASONING else NO_REASONING))
                timeout = self._parent._parent.timeout
                started = time.monotonic()
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                if payload['reasoning'] == NO_REASONING and _reasoning_is_mandatory(response):
                    # Ese modelo no puede dejar de razonar: la llamada rechazada no llegó al modelo y se repite pidiendo lo mínimo.
                    _MANDATORY_REASONING.add(model)
                    logger.info('razonamiento_obligatorio', extra={'model': model})
                    payload['reasoning'] = dict(LEAST_REASONING)
                    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                elapsed_ms = int((time.monotonic() - started) * 1000)
                logger.info('openrouter_call', extra={'model': model, 'status_code': response.status_code, 'elapsed_ms': elapsed_ms})
                if response.status_code >= 400:
                    logger.error('openrouter_error', extra={'model': model, 'status_code': response.status_code, 'error': _error_code(response)})
                response.raise_for_status()
                return response.json()

        @property
        def completions(self):
            return _OpenRouterCompletions.Chat._Completions(self)

    @property
    def chat(self):
        return _OpenRouterCompletions.Chat(self)


class AIService:
    def __init__(self, *, provider: str = 'openrouter', api_key: str | None = None, request_timeout: int | None = None) -> None:
        self.provider = provider
        # No hay clave general: sin la clave de un negocio no se arma ningún cliente.
        self.api_key = self._normalize_api_key(api_key)
        self.request_timeout = request_timeout or settings.llm_timeout_seconds
        self.max_retries = 0
        self.client = self.build_client(provider_override=provider, api_key_override=self.api_key) if self.api_key else None

    @staticmethod
    def _normalize_api_key(value: str | None) -> str:
        token = str(value or '').strip()
        if token in {'', '<<TOKEN>>', '<TOKEN>'}:
            return ''
        return token

    def default_model(self) -> str:
        return settings.openrouter_model

    def build_client(self, provider_override: str | None = None, api_key_override: str | None = None):
        provider = provider_override or self.provider
        if provider != 'openrouter':
            return None
        api_key = self._normalize_api_key(api_key_override or self.api_key)
        logger.info('ai_build_client', extra={'provider': provider, 'api_key_present': bool(api_key)})
        if not api_key:
            logger.warning('ai_build_client_missing_api_key', extra={'provider': provider})
            return None
        return _OpenRouterCompletions(api_key, settings.openrouter_base_url, self.request_timeout, self.max_retries)

    @staticmethod
    def _extract_choice_text(choice):
        if choice is None:
            return None
        if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
            return choice.message.content
        if hasattr(choice, 'text'):
            return choice.text
        if isinstance(choice, dict):
            message = choice.get('message') or {}
            if isinstance(message, dict) and 'content' in message:
                return message.get('content')
            if 'text' in choice:
                return choice.get('text')
        return None

    def generate(self, messages: list[dict], *, model_name: str | None, temperature: float, max_tokens: int | None = None, top_p: float | None = None) -> str:
        if not self.client:
            raise RuntimeError('LLM client not configured')
        model_to_use = model_name or self.default_model()
        logging.info('Using model: %s', model_to_use)
        payload = {'model': model_to_use, 'temperature': temperature, 'messages': messages}
        if max_tokens is not None:
            payload['max_tokens'] = max_tokens
        if top_p is not None:
            payload['top_p'] = top_p
        try:
            response = self.client.chat.completions.create(**payload)
        except TypeError:
            payload.pop('top_p', None)
            try:
                response = self.client.chat.completions.create(**payload)
            except TypeError:
                payload.pop('max_tokens', None)
                response = self.client.chat.completions.create(**payload)
        try:
            first_choice = response.choices[0]
        except Exception:
            first_choice = response['choices'][0] if isinstance(response, dict) and response.get('choices') else None

        usage = response.get('usage') if isinstance(response, dict) else getattr(response, 'usage', None)
        if usage is not None:
            usage_dict = usage if isinstance(usage, dict) else vars(usage)
            logger.info(
                'tokens_usage',
                extra={
                    'model': model_to_use,
                    'prompt_tokens': usage_dict.get('prompt_tokens'),
                    'completion_tokens': usage_dict.get('completion_tokens'),
                    'total_tokens': usage_dict.get('total_tokens'),
                },
            )

        return str(self._extract_choice_text(first_choice) or '').strip()