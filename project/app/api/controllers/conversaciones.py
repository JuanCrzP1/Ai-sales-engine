from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_tenant, get_current_user
from app.api.schemas.conversacion import ConversationMessageCreate, ConversationMessageOut
from app.database.connection import get_db
from app.models import AdminUser, Client, ConversationMessage, MessageDirection, Tenant
from app.application.services.crm_service import CRMService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("/messages", response_model=ConversationMessageOut)
def create_message(
    payload: ConversationMessageCreate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    client = db.query(Client).filter(Client.id == payload.client_id, Client.tenant_id == tenant.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    crm_service = CRMService(db)
    return crm_service.store_message(
        tenant_id=tenant.id,
        client_id=payload.client_id,
        direction=MessageDirection(payload.direction.value),
        message_text=payload.message_text,
        intent=payload.intent,
    )


@router.get("/clients/{client_id}", response_model=list[ConversationMessageOut])
def list_client_messages(
    client_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    client = db.query(Client).filter(Client.id == client_id, Client.tenant_id == tenant.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.client_id == client_id, ConversationMessage.tenant_id == tenant.id)
        .order_by(ConversationMessage.created_at.asc())
        .all()
    )
