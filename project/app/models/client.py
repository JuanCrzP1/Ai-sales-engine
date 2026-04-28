from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import LeadStatus

if TYPE_CHECKING:
	from app.models.conversation_message import ConversationMessage
	from app.models.tenant import Tenant


class Client(Base):
	__tablename__ = "clients"
	__table_args__ = (
		UniqueConstraint("tenant_id", "phone_number", name="uq_client_phone_by_tenant"),
		UniqueConstraint("tenant_id", "client_code", name="uq_client_code_by_tenant"),
	)

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
	client_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
	phone_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
	name: Mapped[str | None] = mapped_column(String(120), nullable=True)
	lead_status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.frio, nullable=False)
	last_intent: Mapped[str | None] = mapped_column(String(80), nullable=True)
	last_contact_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

	tenant: Mapped["Tenant"] = relationship(back_populates="clients")
	messages: Mapped[list["ConversationMessage"]] = relationship(back_populates="client", cascade="all, delete-orphan")


__all__ = ["Client"]
