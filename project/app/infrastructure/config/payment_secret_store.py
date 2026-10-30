"""Datos de pago de cada negocio cifrados en la base de datos (origen `secret_store:`).

El contrato solo guarda referencias `{"secret_ref": "secret_store:<clave>"}`; el valor (link, número,
cuenta o referencia) se cifra con Fernet antes de llegar a la base de datos. La clave se toma de
`BUSINESS_CONFIG_SECRETS_KEY` y no tiene valor por defecto: sin clave no se cifra ni se lee nada.
Estos datos no se mezclan con las credenciales de canales (`tenant_secrets`), que son de las integraciones.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import insert, select, update
from sqlalchemy.engine import Engine

from app.domain.business_config.contract import SecretRef
from app.infrastructure.config.business_config_store import BusinessConfigError
from app.infrastructure.config.business_config_tables import business_config_secrets, tenants
from app.infrastructure.config.payment_secrets import SecretResolutionError

SECRET_STORE_SOURCE = "secret_store"
SECRETS_KEY_ENV = "BUSINESS_CONFIG_SECRETS_KEY"


def _ref_key(ref: str) -> str:
    source, separator, key = ref.partition(":")
    if separator and source == SECRET_STORE_SOURCE and key:
        return key
    raise SecretResolutionError(f"referencia que no pertenece al almacén de secretos: {source or ref!r}")


class PaymentSecretStore:
    def __init__(self, engine: Engine, key: str | None = None) -> None:
        self._engine = engine
        self._key = key

    def _cipher(self) -> Fernet:
        key = self._key if self._key is not None else os.getenv(SECRETS_KEY_ENV, "")
        if not key:
            raise SecretResolutionError(f"falta {SECRETS_KEY_ENV}: los datos de pago no se pueden cifrar ni leer")
        try:
            return Fernet(key.encode("utf-8"))
        except (ValueError, TypeError) as exc:
            raise SecretResolutionError(f"{SECRETS_KEY_ENV} no es una clave Fernet válida") from exc

    def _tenant_id(self, conn, tenant_slug: str):
        tenant_id = conn.execute(select(tenants.c.id).where(tenants.c.slug == tenant_slug)).scalar_one_or_none()
        if tenant_id is None:
            raise BusinessConfigError(f"{tenant_slug}: el negocio no existe en la base de datos")
        return tenant_id

    def put_many(self, tenant_slug: str, secrets: dict[str, str]) -> None:
        """Guarda (o reemplaza) los valores indexados por su referencia `secret_store:<clave>`."""
        cipher = self._cipher()
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            tenant_id = self._tenant_id(conn, tenant_slug)
            for ref, value in secrets.items():
                key = _ref_key(ref)
                ciphertext = cipher.encrypt(str(value).encode("utf-8")).decode("ascii")
                updated = conn.execute(
                    update(business_config_secrets)
                    .where(business_config_secrets.c.tenant_id == tenant_id, business_config_secrets.c.ref_key == key)
                    .values(ciphertext=ciphertext, updated_at=now)
                )
                if updated.rowcount == 0:
                    conn.execute(insert(business_config_secrets).values(tenant_id=tenant_id, ref_key=key, ciphertext=ciphertext))

    def resolver(self, tenant_slug: str):
        """Resolutor de referencias `secret_store:` limitado a los datos de un único negocio."""

        def _resolve(ref: SecretRef) -> str:
            key = _ref_key(ref.secret_ref)
            with self._engine.connect() as conn:
                tenant_id = self._tenant_id(conn, tenant_slug)
                ciphertext = conn.execute(
                    select(business_config_secrets.c.ciphertext).where(
                        business_config_secrets.c.tenant_id == tenant_id, business_config_secrets.c.ref_key == key
                    )
                ).scalar_one_or_none()
            if ciphertext is None:
                raise SecretResolutionError(f"{tenant_slug}: no existe el dato de pago '{key}'")
            try:
                return self._cipher().decrypt(ciphertext.encode("ascii")).decode("utf-8")
            except InvalidToken as exc:
                raise SecretResolutionError(f"{tenant_slug}: el dato de pago '{key}' no se puede descifrar con la clave actual") from exc

        return _resolve
