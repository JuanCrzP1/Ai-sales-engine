from __future__ import annotations

import hashlib
import hmac
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.application.runtime import load_tenant_runtime_yaml
from app.config import settings
from app.connectors.router import route_message
from app.connectors.whatsapp.transport_runtime import WhatsAppService
from app.models import Tenant
from app.services.ai_service import AIService
from app.services.tenant_channel_resolver import get_tenant_by_phone_number_id
from app.utils.logger import logger

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

SIGNATURE_HEADER = "X-Hub-Signature-256"


async def signed_payload(request: Request) -> dict:
    """El cuerpo del webhook, solo si Meta lo firmó con el secreto de la app (`META_APP_SECRET`).

    Sin secreto configurado no se acepta nada: un webhook sin verificar dejaría a cualquiera enviar mensajes falsos.
    """
    secret = str(getattr(settings, "meta_app_secret", "") or "").strip()
    body = await request.body()
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not secret or not hmac.compare_digest(request.headers.get(SIGNATURE_HEADER, ""), expected):
        logger.warning("whatsapp_webhook_rejected", extra={"reason": "firma_no_valida" if secret else "sin_secreto"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Firma no válida")
    try:
        payload = json.loads(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuerpo no válido") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuerpo no válido")
    return payload


def _extract_phone_number_id(payload: dict) -> str:
    try:
        return str(
            payload.get("entry", [])[0]
            .get("changes", [])[0]
            .get("value", {})
            .get("metadata", {})
            .get("phone_number_id")
            or ""
        ).strip()
    except Exception:
        return ""


def _build_tenant(tenant_payload: dict | None) -> Tenant | None:
    if not isinstance(tenant_payload, dict):
        return None

    tenant_slug = str(tenant_payload.get("slug") or "").strip()
    tenant_id = tenant_payload.get("id")
    if not tenant_slug or tenant_id is None:
        return None

    tenant = Tenant(name=tenant_slug, slug=tenant_slug)
    tenant.id = tenant_id
    tenant.is_active = str(tenant_payload.get("status") or "").strip().lower() == "active"
    return tenant


@router.get("/webhook", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> PlainTextResponse:
    expected_token = str(getattr(settings, "meta_verify_token", "") or "").strip()
    # Comparación en tiempo constante; los tokens nunca van a los registros.
    if hub_mode == "subscribe" and expected_token and hmac.compare_digest(str(hub_verify_token or ""), expected_token):
        return PlainTextResponse(str(hub_challenge or ""), status_code=status.HTTP_200_OK)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Webhook verification failed")


@router.post("/webhook")
def receive_whatsapp_webhook(payload: Annotated[dict, Depends(signed_payload)]) -> dict[str, str]:
    if not bool(getattr(settings, "enable_webhook_processing", True)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint no disponible")

    phone_number_id = _extract_phone_number_id(payload)
    tenant_payload = get_tenant_by_phone_number_id(phone_number_id) if phone_number_id else None
    tenant = _build_tenant(tenant_payload)

    logger.info(
        "tenant_resolved: %s",
        getattr(tenant, "id", None),
        extra={"source": "phone_number_id" if tenant is not None else "unresolved_phone_number_id"},
    )

    routed = route_message("whatsapp_meta", payload)
    message_text = str(routed.get("message") or "").strip()
    phone_number = str(routed.get("user_id") or "").strip()

    if tenant is None or not message_text or not phone_number:
        return {"status": "ignored"}

    runtime_yaml = load_tenant_runtime_yaml(tenant.slug, channel="whatsapp")
    service = AIService()
    response, _ai_used, _metadata = service.generate_business_reply(
        tenant=tenant,
        bot_config=None,
        user_message=message_text,
        user_id=phone_number,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        include_metadata=True,
    )

    logger.info("whatsapp_reply", extra={"tenant": tenant.slug})
    WhatsAppService().send_message(tenant=tenant, phone_number=phone_number, message=str(response or ""), provider="meta")
    return {"status": "ok"}