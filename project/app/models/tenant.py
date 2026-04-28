from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
	from app.models.admin_user import AdminUser
	from app.models.bot_config import BotConfig
	from app.models.client import Client
	from app.models.tenant_connector_config import TenantConnectorConfig


class Tenant(Base):
	__tablename__ = "tenants"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	name: Mapped[str] = mapped_column(String(120), nullable=False)
	slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
	whatsapp_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

	admin_users: Mapped[list["AdminUser"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
	bot_config: Mapped["BotConfig | None"] = relationship(back_populates="tenant", uselist=False, cascade="all, delete-orphan")
	connector_configs: Mapped[list["TenantConnectorConfig"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
	clients: Mapped[list["Client"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


__all__ = ["Tenant"]
