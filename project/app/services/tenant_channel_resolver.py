from __future__ import annotations

from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.infrastructure.db.connection import get_engine
from app.utils.helpers import normalize_phone
from app.utils.logger import logger


def _row_to_tenant(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    mapping = row._mapping
    return {
        "id": mapping.get("id"),
        "name": mapping.get("name"),
        "slug": mapping.get("slug"),
        "status": mapping.get("status"),
    }


def _fetch_tenant(query: Any, params: dict[str, Any]) -> dict[str, Any] | None:
    engine = get_engine()

    try:
        with engine.connect() as conn:
            row = conn.execute(query, params).fetchone()
    except SQLAlchemyError:
        logger.warning("tenant_channel_lookup_failed", extra={"params": params})
        return None

    return _row_to_tenant(row)


def get_tenant_by_whatsapp_number(number: str) -> dict[str, Any] | None:
    normalized_number = normalize_phone(number)
    if not normalized_number:
        return None

    query = text("""
        SELECT t.id, t.name, t.slug, t.status
        FROM tenant_channels tc
        JOIN tenants t ON t.id = tc.tenant_id
        WHERE tc.is_active = TRUE
          AND LOWER(COALESCE(tc.channel, '')) LIKE 'whatsapp%'
          AND RIGHT(REGEXP_REPLACE(COALESCE(tc.config ->> 'whatsapp_number', ''), '\\D', '', 'g'), 15) = :number
        LIMIT 1
    """)
    return _fetch_tenant(query, {"number": normalized_number})


def get_tenant_by_phone_number_id(phone_number_id: str) -> dict[str, Any] | None:
    normalized_id = str(phone_number_id or "").strip()
    if not normalized_id:
        return None

    query = text("""
        SELECT t.id, t.name, t.slug, t.status
        FROM tenant_channels tc
        JOIN tenants t ON t.id = tc.tenant_id
        WHERE tc.is_active = TRUE
          AND LOWER(COALESCE(tc.channel, '')) LIKE 'whatsapp%'
          AND COALESCE(tc.config ->> 'phone_number_id', '') = :phone_number_id
        LIMIT 1
    """)
    return _fetch_tenant(query, {"phone_number_id": normalized_id})


def get_whatsapp_channel_config_by_tenant_id(tenant_id: str) -> dict[str, Any] | None:
    normalized_tenant_id = str(tenant_id or "").strip()
    if not normalized_tenant_id:
        return None

    query = text("""
        SELECT tc.config
        FROM tenant_channels tc
        WHERE tc.is_active = TRUE
          AND tc.tenant_id = CAST(:tenant_id AS UUID)
          AND LOWER(COALESCE(tc.channel, '')) LIKE 'whatsapp%'
        LIMIT 1
    """)

    engine = get_engine()
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"tenant_id": normalized_tenant_id}).fetchone()
    except SQLAlchemyError:
        logger.warning("tenant_channel_config_lookup_failed", extra={"tenant_id": normalized_tenant_id})
        return None

    if row is None:
        return None

    config = row._mapping.get("config")
    return config if isinstance(config, dict) else None