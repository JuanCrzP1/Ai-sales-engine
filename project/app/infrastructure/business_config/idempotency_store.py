"""Las respuestas de la API del asistente a los pedidos con `Idempotency-Key` (`api_idempotency`, migración 0012).

Si un sistema repite un pedido (por ejemplo, porque no le llegó la respuesta), recibe exactamente la misma respuesta durante 24
horas, sin volver a gastar la IA. Se guarda cifrada con la clave de los datos de pago (`BUSINESS_CONFIG_SECRETS_KEY`), porque lleva
lo mismo que recibió el cliente. Las de más de 24 horas se borran al guardar otras.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import InvalidToken
from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.infrastructure.business_config.payment_secret_store import check_secrets_key
from app.infrastructure.business_config.tables import api_idempotency
from app.infrastructure.business_config.tenancy import tenant_of

KEEP_FOR = timedelta(hours=24)


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class IdempotencyStore:
    def __init__(self, engine: Engine, key: str | None = None) -> None:
        self._engine = engine
        self._key = key

    def get(self, tenant_slug: str, idempotency_key: str) -> dict[str, Any] | None:
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            row = conn.execute(
                select(api_idempotency.c.response_ciphertext, api_idempotency.c.created_at).where(
                    api_idempotency.c.tenant_id == tenant.id, api_idempotency.c.idempotency_key == idempotency_key
                )
            ).first()
        if row is None or datetime.now(timezone.utc) - _utc(row.created_at) > KEEP_FOR:
            return None
        try:
            return json.loads(check_secrets_key(self._key).decrypt(row.response_ciphertext.encode("ascii")))
        except (InvalidToken, ValueError):
            return None

    def put(self, tenant_slug: str, idempotency_key: str, response: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        ciphertext = check_secrets_key(self._key).encrypt(json.dumps(response, ensure_ascii=False).encode("utf-8")).decode("ascii")
        try:
            with self._engine.begin() as conn:
                tenant = tenant_of(conn, tenant_slug)
                conn.execute(delete(api_idempotency).where(api_idempotency.c.created_at < now - KEEP_FOR))
                conn.execute(
                    insert(api_idempotency).values(tenant_id=tenant.id, idempotency_key=idempotency_key, response_ciphertext=ciphertext, created_at=now)
                )
        except IntegrityError:
            pass  # Ya estaba guardada (otro proceso respondió el mismo pedido): vale la primera.
