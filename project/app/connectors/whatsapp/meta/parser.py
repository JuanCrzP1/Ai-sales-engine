"""Meta (WhatsApp Cloud API) parser skeleton."""
from typing import Dict, Any

from app.connectors.base.base_connector import to_unified_format


def parse(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Meta WhatsApp webhook payload to unified format.

    This implementation is conservative: it attempts to extract the sender and message
    from common Cloud API shapes. Caller/maintainer should extend as needed.
    """
    # Example shapes: payload['entry'][0]['changes'][0]['value']['messages'][0]
    try:
        entry = payload.get("entry", [])
        change = entry[0].get("changes", [])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])
        msg = messages[0]
        sender = msg.get("from") or msg.get("sender")
        text = ""
        if "text" in msg and isinstance(msg["text"], dict):
            text = msg["text"].get("body", "")
        elif "body" in msg:
            text = msg.get("body", "")
    except Exception:
        sender = payload.get("from") or payload.get("phone") or "unknown"
        text = payload.get("text") or payload.get("message") or ""

    return to_unified_format(user_id=str(sender), message=str(text), channel="whatsapp_meta", extras={})
