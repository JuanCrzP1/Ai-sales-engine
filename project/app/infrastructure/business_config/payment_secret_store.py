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
from sqlalchemy.engine import Connection, Engine

from app.domain.business_config.contract import SecretRef
from app.domain.business_config.errors import SecretNotFoundError, SecretResolutionError
from app.domain.business_config.payment_data import SECRET_STORE_SOURCE
from app.infrastructure.business_config.tables import business_config_secrets
from app.infrastructure.business_config.tenancy import tenant_of

SECRETS_KEY_ENV = "BUSINESS_CONFIG_SECRETS_KEY"


def check_secrets_key(key: str | None = None) -> Fernet:
    """El cifrador de la clave indicada o de `BUSINESS_CONFIG_SECRETS_KEY`; falla si falta o no es válida."""
    value = key if key is not None else os.getenv(SECRETS_KEY_ENV, "")
    if not value:
        raise SecretResolutionError(f"falta {SECRETS_KEY_ENV}: los datos de pago no se pueden cifrar ni leer")
    try:
        return Fernet(value.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise SecretResolutionError(f"{SECRETS_KEY_ENV} no es una clave Fernet válida") from exc


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
        return check_secrets_key(self._key)

    def verify_key(self) -> None:
        self._cipher()

    def write(self, conn: Connection, tenant_id, secrets: dict[str, str]) -> None:
        """Guarda (o reemplaza) los valores por su referencia, dentro de la transacción de quien llama."""
        cipher = self._cipher()
        now = datetime.now(timezone.utc)
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

    def put_many(self, tenant_slug: str, secrets: dict[str, str]) -> None:
        """Guarda valores sueltos, sin versión asociada. Una versión y sus datos se guardan juntos con `save_draft`."""
        with self._engine.begin() as conn:
            self.write(conn, tenant_of(conn, tenant_slug).id, secrets)

    def known_values(self, tenant_slug: str) -> list[str]:
        """Los valores guardados de un negocio, para comprobar que no aparecen en sus documentos. Sin clave, falla."""
        with self._engine.connect() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            ciphertexts = conn.execute(
                select(business_config_secrets.c.ciphertext).where(business_config_secrets.c.tenant_id == tenant_id)
            ).scalars().all()
        if not ciphertexts:
            return []
        cipher = self._cipher()
        try:
            return [cipher.decrypt(ciphertext.encode("ascii")).decode("utf-8") for ciphertext in ciphertexts]
        except InvalidToken as exc:
            raise SecretResolutionError(f"{tenant_slug}: los datos de pago no se pueden descifrar con la clave actual") from exc

    def resolver(self, tenant_slug: str):
        """Resolutor de referencias `secret_store:` limitado a los datos de un único negocio."""

        def _resolve(ref: SecretRef) -> str:
            key = _ref_key(ref.secret_ref)
            with self._engine.connect() as conn:
                tenant_id = tenant_of(conn, tenant_slug).id
                ciphertext = conn.execute(
                    select(business_config_secrets.c.ciphertext).where(
                        business_config_secrets.c.tenant_id == tenant_id, business_config_secrets.c.ref_key == key
                    )
                ).scalar_one_or_none()
            if ciphertext is None:
                raise SecretNotFoundError(f"{tenant_slug}: no existe el dato de pago '{key}'")
            try:
                return self._cipher().decrypt(ciphertext.encode("ascii")).decode("utf-8")
            except InvalidToken as exc:
                raise SecretResolutionError(f"{tenant_slug}: el dato de pago '{key}' no se puede descifrar con la clave actual") from exc

        return _resolve
