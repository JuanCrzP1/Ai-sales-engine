"""Las suscripciones a notificaciones de cada persona (`push_subscriptions`) y las claves VAPID de la plataforma (`platform_keys`).

Las claves VAPID identifican a la plataforma ante los servicios de notificaciones. Se crean solas la primera vez que hacen falta y la
parte secreta se guarda cifrada con la clave de los datos de pago (`BUSINESS_CONFIG_SECRETS_KEY`): no hay que configurar nada. Si dos
procesos las crean a la vez, queda la primera y ambos usan esa.
"""
from __future__ import annotations

import base64
import uuid
from collections.abc import Collection
from datetime import datetime, timezone

from cryptography.fernet import InvalidToken
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.errors import SecretResolutionError
from app.domain.business_config.push import PushSubscription, VapidKeys
from app.infrastructure.business_config.payment_secret_store import check_secrets_key
from app.infrastructure.business_config.tables import platform_keys, push_subscriptions

VAPID_KEY_NAME = "web_push_vapid"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def new_vapid_keys() -> VapidKeys:
    private = ec.generate_private_key(ec.SECP256R1())
    public = private.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return VapidKeys(public_key=_b64url(public), private_key=_b64url(private.private_numbers().private_value.to_bytes(32, "big")))


class PushStore:
    def __init__(self, engine: Engine, key: str | None = None) -> None:
        self._engine = engine
        self._key = key

    # ------------------------------------------------------------------ claves de la plataforma

    def vapid_public_key(self) -> str:
        return self._vapid(need_private=False).public_key

    def vapid_keys(self) -> VapidKeys:
        return self._vapid(need_private=True)

    def _vapid(self, *, need_private: bool) -> VapidKeys:
        cipher = check_secrets_key(self._key)
        with self._engine.connect() as conn:
            row = conn.execute(select(platform_keys).where(platform_keys.c.name == VAPID_KEY_NAME)).first()
        if row is None:
            created = new_vapid_keys()
            try:
                with self._engine.begin() as conn:
                    conn.execute(
                        insert(platform_keys).values(
                            name=VAPID_KEY_NAME, public_value=created.public_key,
                            secret_ciphertext=cipher.encrypt(created.private_key.encode("ascii")).decode("ascii"),
                            created_at=datetime.now(timezone.utc),
                        )
                    )
                return created
            except IntegrityError:
                # Otro proceso las creó a la vez: se usan las suyas.
                with self._engine.connect() as conn:
                    row = conn.execute(select(platform_keys).where(platform_keys.c.name == VAPID_KEY_NAME)).one()
        if not need_private:
            return VapidKeys(public_key=row.public_value, private_key="")
        try:
            private = cipher.decrypt(row.secret_ciphertext.encode("ascii")).decode("ascii")
        except InvalidToken as exc:
            raise SecretResolutionError("las claves de las notificaciones no se pueden descifrar con la clave de cifrado actual") from exc
        return VapidKeys(public_key=row.public_value, private_key=private)

    # ------------------------------------------------------------------ suscripciones

    def subscribe(self, subscription: PushSubscription) -> None:
        """Guarda la suscripción de este navegador. Si la dirección ya existía (otra cuenta en el mismo navegador), pasa a esta."""
        now = datetime.now(timezone.utc)
        values = {"user_id": subscription.user_id, "p256dh": subscription.p256dh, "auth": subscription.auth, "device": subscription.device}
        for attempt in range(2):
            try:
                with self._engine.begin() as conn:
                    key = push_subscriptions.c.endpoint == subscription.endpoint
                    if conn.execute(select(push_subscriptions.c.id).where(key)).first() is None:
                        conn.execute(insert(push_subscriptions).values(id=uuid.uuid4(), endpoint=subscription.endpoint, created_at=now, **values))
                    else:
                        conn.execute(update(push_subscriptions).where(key).values(**values))
                return
            except IntegrityError:
                if attempt:
                    raise

    def unsubscribe(self, user_id: str, endpoint: str) -> bool:
        with self._engine.begin() as conn:
            result = conn.execute(delete(push_subscriptions).where(push_subscriptions.c.user_id == user_id, push_subscriptions.c.endpoint == endpoint))
        return bool(result.rowcount)

    def is_subscribed(self, user_id: str, endpoint: str) -> bool:
        with self._engine.connect() as conn:
            return conn.execute(
                select(push_subscriptions.c.id).where(push_subscriptions.c.user_id == user_id, push_subscriptions.c.endpoint == endpoint)
            ).first() is not None

    def subscriptions_for(self, user_ids: Collection[str]) -> list[PushSubscription]:
        ids = [str(user) for user in user_ids if str(user or "").strip()]
        if not ids:
            return []
        query = select(push_subscriptions).where(push_subscriptions.c.user_id.in_(ids)).order_by(push_subscriptions.c.created_at)
        with self._engine.connect() as conn:
            return [PushSubscription(row.endpoint, row.p256dh, row.auth, row.user_id, row.device) for row in conn.execute(query)]

    def forget(self, endpoint: str) -> None:
        """El servicio dijo que esa suscripción ya no existe (el navegador la quitó): se borra."""
        with self._engine.begin() as conn:
            conn.execute(delete(push_subscriptions).where(push_subscriptions.c.endpoint == endpoint))

    def mark_delivered(self, endpoint: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(update(push_subscriptions).where(push_subscriptions.c.endpoint == endpoint).values(last_success_at=datetime.now(timezone.utc)))
