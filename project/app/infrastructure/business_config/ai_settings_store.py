"""Inteligencia artificial de cada negocio en la base: su modelo y su clave cifrada (`business_ai_settings`).

La clave se cifra con la misma clave Fernet que los datos de pago (`BUSINESS_CONFIG_SECRETS_KEY`) y solo se descifra para
entregársela al motor. Cada operación recibe el negocio y solo alcanza su fila: un negocio nunca lee la clave de otro.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import InvalidToken
from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection, Engine

from app.domain.business_config.ai_settings import AI_PROVIDER, AICredentials, AISettings, key_hint
from app.domain.business_config.errors import SecretResolutionError
from app.infrastructure.business_config.payment_secret_store import check_secrets_key
from app.infrastructure.business_config.tables import business_ai_settings
from app.infrastructure.business_config.tenancy import tenant_of


class AISettingsStore:
    def __init__(self, engine: Engine, key: str | None = None) -> None:
        self._engine = engine
        self._key = key

    @staticmethod
    def _row(conn: Connection, tenant_slug: str) -> tuple[Any, Any]:
        tenant_id = tenant_of(conn, tenant_slug).id
        row = conn.execute(select(business_ai_settings).where(business_ai_settings.c.tenant_id == tenant_id)).first()
        return tenant_id, row

    def ai_settings(self, tenant_slug: str) -> AISettings:
        with self._engine.connect() as conn:
            _tenant_id, row = self._row(conn, tenant_slug)
        if row is None:
            return AISettings()
        return AISettings(provider=row.provider, model=row.model, key_configured=row.key_ciphertext is not None, key_hint=row.key_hint)

    def ai_credentials(self, tenant_slug: str) -> AICredentials | None:
        with self._engine.connect() as conn:
            _tenant_id, row = self._row(conn, tenant_slug)
        if row is None or row.key_ciphertext is None:
            return None
        try:
            api_key = check_secrets_key(self._key).decrypt(row.key_ciphertext.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise SecretResolutionError("la clave de IA de este negocio no se puede descifrar con la clave de cifrado actual") from exc
        return AICredentials(provider=row.provider, model=row.model, api_key=api_key)

    def save_ai_settings(self, tenant_slug: str, *, model: str | None, api_key: str | None, clear_key: bool) -> AISettings:
        """Guarda el modelo y, si llega, la clave nueva cifrada. Sin clave nueva, conserva la guardada salvo `clear_key`."""
        cipher = check_secrets_key(self._key) if api_key else None
        values: dict[str, Any] = {"provider": AI_PROVIDER, "model": model, "updated_at": datetime.now(timezone.utc)}
        if cipher is not None and api_key:
            values.update(key_ciphertext=cipher.encrypt(api_key.encode("utf-8")).decode("ascii"), key_hint=key_hint(api_key))
        elif clear_key:
            values.update(key_ciphertext=None, key_hint=None)
        with self._engine.begin() as conn:
            tenant_id, row = self._row(conn, tenant_slug)
            if row is None:
                conn.execute(insert(business_ai_settings).values(tenant_id=tenant_id, **values))
            else:
                conn.execute(update(business_ai_settings).where(business_ai_settings.c.tenant_id == tenant_id).values(**values))
        return self.ai_settings(tenant_slug)
