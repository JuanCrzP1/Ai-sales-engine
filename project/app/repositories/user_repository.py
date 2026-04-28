from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer

from app.models import Client
from app.utils.helpers import normalize_phone
from app.utils.logger import logger


class UserRepository:
    MAX_CLIENT_CODE_RETRIES = 3

    def __init__(self, db: Session):
        self.db = db

    def get_by_phone(self, tenant_id: int, phone_number: str) -> Client | None:
        normalized_phone = normalize_phone(phone_number)
        return (
            self.db.query(Client)
            .filter(Client.tenant_id == tenant_id, Client.phone_number == normalized_phone)
            .first()
        )

    def get_by_id(self, client_id: int, tenant_id: int | None = None) -> Client | None:
        query = self.db.query(Client).filter(Client.id == client_id)
        if tenant_id is not None:
            query = query.filter(Client.tenant_id == tenant_id)
        return query.first()

    def get_or_create(self, tenant_id: int, phone_number: str, name: str | None = None) -> Client:
        normalized_phone = normalize_phone(phone_number)
        client = self.get_by_phone(tenant_id=tenant_id, phone_number=normalized_phone)
        if client is None:
            last_error: IntegrityError | None = None
            for attempt in range(1, self.MAX_CLIENT_CODE_RETRIES + 1):
                client = Client(
                    tenant_id=tenant_id,
                    client_code=self._generate_next_client_code(tenant_id),
                    phone_number=normalized_phone,
                    name=name,
                )
                self.db.add(client)
                try:
                    self.db.commit()
                    self.db.refresh(client)
                    return client
                except IntegrityError as exc:
                    self.db.rollback()
                    last_error = exc
                    existing = self.get_by_phone(tenant_id=tenant_id, phone_number=normalized_phone)
                    if existing is not None:
                        return existing
                    logger.warning(
                        'client_code_collision_retry',
                        extra={
                            'tenant_id': tenant_id,
                            'phone_number': normalized_phone,
                            'attempt': attempt,
                        },
                    )
                except Exception:
                    self.db.rollback()
                    logger.exception('user_repository_commit_failed')
                    raise
            if last_error is not None:
                logger.exception('user_repository_client_code_exhausted')
                raise last_error

        if not getattr(client, "client_code", None):
            client.client_code = self._generate_next_client_code(tenant_id)
        if name and not client.name:
            client.name = name
        self._commit()
        self.db.refresh(client)
        return client

    def save(self, client: Client) -> Client:
        self._commit()
        self.db.refresh(client)
        return client

    def build_context(self, client: Client) -> dict:
        return {
            "client_id": client.id,
            "client_code": client.client_code,
            "tenant_id": client.tenant_id,
            "phone_number": client.phone_number,
            "name": client.name,
            "lead_status": client.lead_status.value if client.lead_status else None,
            "last_intent": client.last_intent,
            "last_contact_at": client.last_contact_at.isoformat() if client.last_contact_at else None,
        }

    def _generate_next_client_code(self, tenant_id: int) -> str:
        current_max = (
            self.db.query(func.max(cast(Client.client_code, Integer)))
            .filter(Client.tenant_id == tenant_id)
            .scalar()
        )
        next_number = int(current_max or 0) + 1
        return f"{next_number:03d}"

    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception("user_repository_commit_failed")
            raise
