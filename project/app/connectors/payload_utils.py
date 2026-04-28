from __future__ import annotations

from copy import deepcopy
from typing import Any


def coerce_outbound_payload(message: str | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(message, dict):
        payload = deepcopy(message)
    else:
        payload = {'text': message or ''}

    payload.setdefault('text', '')
    payload.setdefault('media', [])
    payload.setdefault('menu', None)
    payload.setdefault('fallback_text', payload.get('text', '') or '')
    payload.setdefault('source_key', None)
    payload.setdefault('metadata', {})
    return payload


def render_text_fallback(payload: str | dict[str, Any] | None) -> str:
    normalized = coerce_outbound_payload(payload)
    parts: list[str] = []

    text = str(normalized.get('text') or '').strip()
    if text:
        parts.append(text)

    menu = normalized.get('menu')
    menu_fallback = ''
    if isinstance(menu, dict):
        menu_fallback = str(menu.get('fallback_text') or '').strip()
    if menu_fallback and menu_fallback not in parts:
        parts.append(menu_fallback)

    if not parts:
        for media in normalized.get('media', []):
            caption = str((media or {}).get('caption') or '').strip()
            if caption:
                parts.append(caption)

    fallback = '\n\n'.join(part for part in parts if part).strip()
    return fallback or text
