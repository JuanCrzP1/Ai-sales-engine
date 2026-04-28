from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import ConversationMessage, MessageDirection
from app.utils.logger import logger


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        tenant_id: int,
        client_id: int,
        direction: MessageDirection,
        message_text: str,
        intent: str | None = None,
        ai_used: bool = False,
        channel: str = "whatsapp",
    ) -> ConversationMessage:
        message = ConversationMessage(
            tenant_id=tenant_id,
            client_id=client_id,
            direction=direction,
            channel=channel,
            message_text=message_text,
            intent=intent,
            ai_used=ai_used,
        )
        self.db.add(message)
        self._commit()
        self.db.refresh(message)
        return message

    def list_recent(self, client_id: int, limit: int = 8) -> list[ConversationMessage]:
        messages = (
            self.db.query(ConversationMessage)
            .filter(ConversationMessage.client_id == client_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))

    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception("message_repository_commit_failed")
            raise
