"""Base connector interfaces and helpers for all connectors."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseConnector(ABC):
    """Abstract base class every connector should implement.

    Responsibilities:
    - parse_webhook(payload) -> returns unified message dict
    - send_message(tenant, user_id, message) -> bool
    """

    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def send_message(self, tenant: Any, user_id: str, message: str) -> bool:
        raise NotImplementedError()


def to_unified_format(user_id: str, message: str, channel: str, extras: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Return the unified message format used by ConversationService.

    Format:
    {
      "user_id": "...",
      "message": "...",
            "channel": "whatsapp_meta|instagram",
      ... extras
    }
    """
    out = {"user_id": user_id, "message": message, "channel": channel}
    if extras:
        out.update(extras)
    return out
