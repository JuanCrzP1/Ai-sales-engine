from __future__ import annotations

import logging
import requests

from app.config import settings
from app.utils.logger import logger


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
                extra_params = {key: value for key, value in (kwargs or {}).items()}
                logger.info(
                    'openrouter_request_payload',
                    extra={
                        'url': url,
                        'model': model,
                        'messages': messages,
                        'temperature': temperature,
                        'max_tokens': payload.get('max_tokens'),
                        'extra_params': extra_params,
                        'payload': payload,
                    },
                )
                logger.info('AI_CALL_COUNT: 1', extra={'provider': 'openrouter', 'model': model})
                response = requests.post(url, headers=headers, json=payload, timeout=self._parent._parent.timeout)
                response_preview = response.text[:4000]
                logger.info(
                    'openrouter_response_status',
                    extra={
                        'status_code': response.status_code,
                        'model': model,
                        'attempt': 1,
                        'response_body_preview': response_preview,
                    },
                )
                if response.status_code >= 400:
                    logger.error(
                        'openrouter_response_error',
                        extra={
                            'status_code': response.status_code,
                            'model': model,
                            'payload': payload,
                            'response_body': response_preview,
                        },
                    )
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
        self.api_key = self._normalize_api_key(api_key or settings.openrouter_api_key)
        self.request_timeout = request_timeout or settings.llm_timeout_seconds
        self.max_retries = 0
        self.client = self.build_client(provider_override=provider, api_key_override=self.api_key)

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