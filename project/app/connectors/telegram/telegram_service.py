from __future__ import annotations

import os

from app.application.runtime import load_tenant_runtime_yaml
from app.connectors.tenant_guard import resolve_connector_tenant
from app.connectors.router import route_message
from app.models.tenant import Tenant
from app.services.ai_service import AIService


class TelegramService:
    """Telegram adapter that reuses the same AIService pipeline as WhatsApp."""

    def __init__(self, ai_service: AIService | None = None, tenant_slug: str | None = None) -> None:
        self.ai_service = ai_service or AIService()
        self.tenant_slug = resolve_connector_tenant(tenant_slug)

    def _tenant(self) -> Tenant:
        return Tenant(name="Telegram Test", slug=self.tenant_slug)

    @staticmethod
    def _normalize_user_id(value: str) -> str:
        return str(value or "telegram-user").strip() or "telegram-user"

    @staticmethod
    def _normalize_message(value: str) -> str:
        return str(value or "").strip()

    def _route_incoming(self, *, text: str, user_id: str) -> dict:
        payload = {
            "from": self._normalize_user_id(user_id),
            "text": self._normalize_message(text),
            "channel": "telegram",
        }
        return route_message("telegram", payload)

    def _debug_sales_payload(self, *, user_message: str) -> None:
        if str(os.getenv("TELEGRAM_DEBUG_PAYLOAD") or "0").strip() != "1":
            return
        runtime_yaml = load_tenant_runtime_yaml(self.tenant_slug, channel="telegram")
        _sales_cfg, _pricing_cfg, _decision, payload = self.ai_service.pipeline.sales_flow.build(
            tenant_slug=self.tenant_slug,
            user_message=user_message,
            runtime_yaml=runtime_yaml,
        )
        print("DEBUG TELEGRAM PAYLOAD:", payload)

    def handle_message_with_meta(self, text: str, user_id: str) -> tuple[str, bool]:
        routed = self._route_incoming(text=text, user_id=user_id)
        message = self._normalize_message(routed.get("message"))
        sender = self._normalize_user_id(routed.get("user_id"))
        runtime_yaml = load_tenant_runtime_yaml(self.tenant_slug, channel="telegram")
        tenant = self._tenant()

        self._debug_sales_payload(user_message=message)
        print("YAML ENTRANTE:", runtime_yaml.keys())

        response, ai_used = self.ai_service.generate_business_reply(
            tenant=tenant,
            bot_config=None,
            user_message=message,
            user_id=sender,
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
        )
        return str(response or ""), bool(ai_used)

    def handle_message(self, text: str, user_id: str) -> str:
        response, _ai_used = self.handle_message_with_meta(text=text, user_id=user_id)
        return str(response or "")


def handle_message(text: str, user_id: str) -> str:
    service = TelegramService(tenant_slug=os.getenv("TENANT_SLUG"))
    return service.handle_message(text=text, user_id=user_id)
