from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
	from app.models.tenant import Tenant


class BotConfig(Base):
	__tablename__ = "bot_configs"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, unique=True)
	company_name: Mapped[str] = mapped_column(String(120), default="Mi Negocio", nullable=False)
	system_prompt: Mapped[str] = mapped_column(Text, default="Eres un asesor comercial claro, breve y útil.", nullable=False)
	greeting_message: Mapped[str] = mapped_column(Text, default="Hola, gracias por escribirnos. ¿En qué te ayudo?", nullable=False)
	fallback_message: Mapped[str] = mapped_column(Text, default="Puedo ayudarte con precios, horarios, ubicación, productos y seguimiento.", nullable=False)
	sensitive_fallback: Mapped[str] = mapped_column(Text, default="Te confirmo ese dato con el negocio y te respondo en un momento.", nullable=False)
	model_name: Mapped[str] = mapped_column(String(80), default="meta-llama/llama-3.1-8b-instruct", nullable=False)
	openrouter_api_key: Mapped[str | None] = mapped_column("groq_api_key", Text, nullable=True)
	temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
	llm_timeout_seconds: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
	enable_ai_engine: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	enable_optimizer: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

	tenant: Mapped["Tenant"] = relationship(back_populates="bot_config")


__all__ = ["BotConfig"]
