from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.db.connection import get_engine
from app.utils.logger import logger


def get_whatsapp_token(tenant_id: str) -> str | None:
    normalized_tenant_id = str(tenant_id or "").strip()
    if not normalized_tenant_id:
        return None

    query = text("""
        SELECT encrypted_data
        FROM tenant_secrets
        WHERE tenant_id = :tenant_id
        LIMIT 1
    """)

    try:
        with get_engine().connect() as conn:
            row = conn.execute(query, {"tenant_id": normalized_tenant_id}).fetchone()
    except SQLAlchemyError:
        logger.warning("tenant_secrets_lookup_failed", extra={"tenant_id": normalized_tenant_id})
        return None

    if row is None:
        raise Exception("❌ NO ACCESS TOKEN FOUND FOR TENANT")

    raw_value: Any = row._mapping.get("encrypted_data")
    if raw_value is None:
        raise Exception("❌ NO ACCESS TOKEN FOUND FOR TENANT")

    if isinstance(raw_value, memoryview):
        raw_value = raw_value.tobytes()

    if isinstance(raw_value, bytes):
        try:
            raw_value = raw_value.decode("utf-8")
        except UnicodeDecodeError:
            logger.warning("tenant_secrets_decode_failed", extra={"tenant_id": normalized_tenant_id})
            return None

    if isinstance(raw_value, str):
        try:
            payload = json.loads(raw_value)
        except json.JSONDecodeError:
            logger.warning("tenant_secrets_parse_failed", extra={"tenant_id": normalized_tenant_id})
            return None
    elif isinstance(raw_value, dict):
        payload = raw_value
    else:
        return None

    data = payload or {}

    token = data.get("access_token")

    if not token:
        token = data.get("whatsapp", {}).get("access_token")

    if not token:
        raise Exception("❌ NO ACCESS TOKEN FOUND FOR TENANT")

    return str(token).strip()
