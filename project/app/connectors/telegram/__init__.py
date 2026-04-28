"""Telegram connector adapter for local testing."""

from .telegram_service import TelegramService, handle_message

__all__ = ["TelegramService", "handle_message"]
