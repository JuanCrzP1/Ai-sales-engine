from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import TenantConnectorConfig


class TenantConnectorRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_tenant(self, tenant_id: int) -> list[TenantConnectorConfig]:
        return (
            self.db.query(TenantConnectorConfig)
            .filter(TenantConnectorConfig.tenant_id == tenant_id)
            .order_by(TenantConnectorConfig.channel.asc(), TenantConnectorConfig.provider.asc())
            .all()
        )

    def get_by_tenant_channel_provider(self, tenant_id: int, channel: str, provider: str) -> TenantConnectorConfig | None:
        return (
            self.db.query(TenantConnectorConfig)
            .filter(
                TenantConnectorConfig.tenant_id == tenant_id,
                TenantConnectorConfig.channel == channel,
                TenantConnectorConfig.provider == provider,
            )
            .first()
        )

    def save(self, record: TenantConnectorConfig) -> TenantConnectorConfig:
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record


__all__ = ["TenantConnectorRepository"]