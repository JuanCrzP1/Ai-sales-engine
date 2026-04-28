from sqlalchemy.orm import Session

from app.models import Client, ConversationMessage, MessageDirection
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.utils.helpers import normalize_phone


# ================================
# AI-FIRST MODULE
# -------------------------------
# Este modulo NO usa logica por palabras.
# Este modulo NO reescribe respuestas.
# La IA es la unica responsable del contenido.
# ================================


class CRMService:
    def __init__(
        self,
        db: Session,
        user_repository: UserRepository | None = None,
        message_repository: MessageRepository | None = None,
    ):
        self.db = db
        self.user_repository = user_repository or UserRepository(db)
        self.message_repository = message_repository or MessageRepository(db)

    def get_or_create_client(self, tenant_id: int, phone_number: str, name: str | None = None) -> Client:
        normalized_phone = normalize_phone(phone_number)
        return self.user_repository.get_or_create(tenant_id=tenant_id, phone_number=normalized_phone, name=name)

    def store_message(
        self,
        tenant_id: int,
        client_id: int,
        direction: MessageDirection,
        message_text: str,
        intent: str | None = None,
        ai_used: bool = False,
    ) -> ConversationMessage:
        return self.message_repository.create(
            tenant_id=tenant_id,
            client_id=client_id,
            direction=direction,
            message_text=message_text,
            intent=intent,
            ai_used=ai_used,
        )

    def get_recent_history(self, client_id: int, limit: int = 8) -> list[ConversationMessage]:
        return self.message_repository.list_recent(client_id=client_id, limit=limit)
