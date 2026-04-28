"""Central router for incoming messages from different connectors.

The router delegates parsing to connector parsers and returns the unified format.
"""
from typing import Any, Dict

from app.connectors.base.base_connector import to_unified_format


def route_message(channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Route incoming webhook payload to the correct connector parser.

    Returns unified message dict.
    """
    channel = channel.lower()
    if channel == "whatsapp_meta":
        from app.connectors.whatsapp.meta import parser as meta_parser

        return meta_parser.parse(payload)

    # Default: attempt to normalize minimal fields
    user = payload.get("from") or payload.get("From") or payload.get("user")
    text = payload.get("text") or payload.get("Body") or payload.get("message") or ""
    return to_unified_format(user_id=str(user), message=str(text), channel=channel)


def get_sender(channel: str, provider: str | None = None, tenant: Any | None = None):
    """Return the sender module for a given channel/provider or None if missing.

    Expected sender modules expose a `send(tenant, phone_number, message)` function.
    """
    channel = channel.lower()
    if channel == "whatsapp":
        if provider in ("meta", None):
            try:
                from app.connectors.whatsapp.meta import sender as meta_sender
                if tenant is None or not hasattr(meta_sender, "can_send") or meta_sender.can_send(tenant=tenant):
                    return meta_sender
            except Exception:
                pass

    return None
