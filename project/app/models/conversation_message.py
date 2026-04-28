from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import MessageDirection

if TYPE_CHECKING:
	from app.models.client import Client


class ConversationMessage(Base):
	__tablename__ = "conversation_messages"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
	client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
	direction: Mapped[MessageDirection] = mapped_column(Enum(MessageDirection), nullable=False)
	channel: Mapped[str] = mapped_column(String(32), default="whatsapp", nullable=False)
	message_text: Mapped[str] = mapped_column(Text, nullable=False)
	intent: Mapped[str | None] = mapped_column(String(80), nullable=True)
	ai_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

	client: Mapped["Client"] = relationship(back_populates="messages")


__all__ = ["ConversationMessage"]
