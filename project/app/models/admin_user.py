from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
	from app.models.tenant import Tenant


class AdminUser(Base):
	__tablename__ = "admin_users"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
	email: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
	full_name: Mapped[str] = mapped_column(String(120), nullable=False)
	password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

	tenant: Mapped["Tenant"] = relationship(back_populates="admin_users")


__all__ = ["AdminUser"]
