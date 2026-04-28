"""Configuration helpers for Meta WhatsApp connector."""
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.infrastructure.db.connection import get_engine


def get_meta_settings(tenant=None) -> dict:
    if tenant is None:
        return {
            "access_token": getattr(settings, "meta_access_token", ""),
            "phone_number_id": getattr(settings, "meta_phone_number_id", ""),
            "verify_token": getattr(settings, "meta_verify_token", ""),
            "app_secret": getattr(settings, "meta_app_secret", ""),
            "business_account_id": getattr(settings, "meta_business_account_id", ""),
        }

    tenant_id = getattr(tenant, "id", None)
    normalized_tenant_id = str(tenant_id or "").strip()
    if not normalized_tenant_id:
        raise Exception("❌ NO PHONE_NUMBER_ID CONFIGURED")

    query = text("""
        SELECT config
        FROM tenant_channels
        WHERE tenant_id = :tenant_id
          AND channel = 'whatsapp_meta'
          AND is_active = true
        LIMIT 1
    """)

    try:
        with get_engine().connect() as conn:
            row = conn.execute(query, {"tenant_id": normalized_tenant_id}).fetchone()
    except SQLAlchemyError as exc:
        raise Exception("❌ NO PHONE_NUMBER_ID CONFIGURED") from exc

    config = row._mapping.get("config") if row is not None else {}
    config = config if isinstance(config, dict) else {}

    phone_number_id = config.get("phone_number_id")

    if not phone_number_id:
        raise Exception("❌ NO PHONE_NUMBER_ID CONFIGURED")

    return {
        "phone_number_id": str(phone_number_id).strip(),
        "verify_token": getattr(settings, "meta_verify_token", ""),
        "app_secret": getattr(settings, "meta_app_secret", ""),
        "business_account_id": getattr(settings, "meta_business_account_id", ""),
    }
