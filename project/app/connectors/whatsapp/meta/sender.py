"""Meta WhatsApp sender skeleton for WhatsApp Cloud API (Meta)."""
import sys
from typing import Any
import httpx

from app.connectors.payload_utils import coerce_outbound_payload
from app.connectors.whatsapp.meta.config import get_meta_settings
from app.services.tenant_channel_resolver import get_whatsapp_channel_config_by_tenant_id
from app.services.tenant_secrets_service import get_whatsapp_token
from app.utils.logger import logger


def _safe_print(*parts: object) -> None:
    text = " ".join(str(part) for part in parts)
    stdout_encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(stdout_encoding, errors="ignore").decode(stdout_encoding, errors="ignore"))


def _get_tenant_id(tenant: Any) -> str | None:
    if tenant is None:
        return None

    tenant_id = getattr(tenant, "id", None)
    if tenant_id is None and isinstance(tenant, dict):
        tenant_id = tenant.get("id")

    normalized_tenant_id = str(tenant_id or "").strip()
    return normalized_tenant_id or None


def _resolve_access_token(tenant: Any, fallback_token: str | None, *, log_source: bool) -> str | None:
    tenant_id = _get_tenant_id(tenant)
    tenant_token = get_whatsapp_token(tenant_id) if tenant_id else None

    if log_source:
        logger.info(
            "whatsapp_token_source: %s",
            "tenant",
            extra={"tenant_id": tenant_id},
        )

    return tenant_token


def _resolve_phone_number_id(tenant: Any, fallback_phone_id: str | None) -> str | None:
    tenant_id = _get_tenant_id(tenant)
    channel_config = get_whatsapp_channel_config_by_tenant_id(tenant_id) if tenant_id else None
    phone_number_id = fallback_phone_id
    if isinstance(channel_config, dict) and channel_config.get("phone_number_id"):
        phone_number_id = channel_config.get("phone_number_id")

    normalized_phone_id = str(phone_number_id or "").strip()
    return normalized_phone_id or None


def _resolve_meta_runtime(tenant: Any) -> tuple[str | None, str | None]:
    cfg = get_meta_settings(tenant=tenant)

    access_token = _resolve_access_token(tenant, cfg.get("access_token"), log_source=True)
    phone_number_id = _resolve_phone_number_id(tenant, cfg.get("phone_number_id"))
    logger.info(
        "USING WHATSAPP CONFIG",
        extra={
            "tenant_id": _get_tenant_id(tenant),
            "phone_number_id": phone_number_id,
            "token_source": "tenant",
        },
    )
    return access_token, phone_number_id


def can_send(tenant: Any = None) -> bool:
    access_token, phone_number_id = _resolve_meta_runtime(tenant)
    return bool(access_token and phone_number_id)


def _post_meta_message(endpoint: str, headers: dict[str, str], payload: dict[str, Any]) -> None:
    _safe_print("PAYLOAD:", payload)
    resp = httpx.post(endpoint, json=payload, headers=headers, timeout=20.0)
    _safe_print("META STATUS:", resp.status_code)
    _safe_print("META RESPONSE:", resp.text)
    resp.raise_for_status()


def _send_text(endpoint: str, headers: dict[str, str], phone_number: str, text: str) -> None:
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": text},
    }
    _post_meta_message(endpoint, headers, payload)


def _send_image(endpoint: str, headers: dict[str, str], phone_number: str, media: dict[str, Any]) -> None:
    image_payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "image",
        "image": {
            "link": media.get('url'),
            "caption": media.get('caption') or '',
        },
    }
    _post_meta_message(endpoint, headers, image_payload)


def _send_menu(endpoint: str, headers: dict[str, str], phone_number: str, menu: dict[str, Any], text: str) -> None:
    menu_type = str(menu.get('type') or 'buttons').lower()
    body_text = str(menu.get('body') or text or '').strip() or 'Selecciona una opción.'
    footer = str(menu.get('footer') or '').strip()
    title = str(menu.get('title') or '').strip()
    items = menu.get('items', []) if isinstance(menu.get('items'), list) else []

    interactive: dict[str, Any]
    if menu_type == 'list':
        rows = []
        for item in items[:10]:
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    'id': str(item.get('id') or item.get('title') or ''),
                    'title': str(item.get('title') or '')[:24],
                    'description': str(item.get('description') or '')[:72],
                }
            )
        interactive = {
            'type': 'list',
            'body': {'text': body_text},
            'action': {
                'button': str(menu.get('button_text') or 'Ver opciones')[:20],
                'sections': [{'title': title or 'Opciones', 'rows': rows}],
            },
        }
    else:
        buttons = []
        for item in items[:3]:
            if not isinstance(item, dict):
                continue
            buttons.append(
                {
                    'type': 'reply',
                    'reply': {
                        'id': str(item.get('id') or item.get('title') or ''),
                        'title': str(item.get('title') or '')[:20],
                    },
                }
            )
        interactive = {
            'type': 'button',
            'body': {'text': body_text},
            'action': {'buttons': buttons},
        }

    if footer:
        interactive['footer'] = {'text': footer}

    payload = {
        'messaging_product': 'whatsapp',
        'to': phone_number,
        'type': 'interactive',
        'interactive': interactive,
    }
    _post_meta_message(endpoint, headers, payload)


def send(tenant: Any, phone_number: str, message: str | dict[str, Any]) -> bool:
    """Send text, media and interactive menus via Meta Cloud API when present."""
    access_token, phone_id = _resolve_meta_runtime(tenant)
    _safe_print("TOKEN USADO:", access_token)
    _safe_print("PHONE_NUMBER_ID:", phone_id)
    if not access_token or not phone_id:
        raise Exception("❌ WHATSAPP MESSAGE NOT SENT — CONFIG INVALID")

    outbound_payload = coerce_outbound_payload(message)
    endpoint = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    for media in outbound_payload.get('media', []):
        if (media or {}).get('type') == 'image' and (media or {}).get('url'):
            _send_image(endpoint, headers, phone_number, media)

    menu = outbound_payload.get('menu')
    if isinstance(menu, dict):
        _send_menu(endpoint, headers, phone_number, menu, str(outbound_payload.get('text') or ''))
    elif outbound_payload.get('text'):
        _send_text(endpoint, headers, phone_number, str(outbound_payload.get('text') or ''))
    return True
