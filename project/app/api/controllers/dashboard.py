from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_tenant, get_current_user
from app.api.schemas.dashboard import DashboardMetrics
from app.database.connection import get_db
from app.models import AdminUser, Client, ConversationMessage, LeadStatus, Tenant

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def get_metrics(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    total_clients = db.query(func.count(Client.id)).filter(Client.tenant_id == tenant.id).scalar() or 0
    cold_leads = db.query(func.count(Client.id)).filter(Client.tenant_id == tenant.id, Client.lead_status == LeadStatus.frio).scalar() or 0
    warm_leads = db.query(func.count(Client.id)).filter(Client.tenant_id == tenant.id, Client.lead_status == LeadStatus.interesado).scalar() or 0
    hot_leads = db.query(func.count(Client.id)).filter(Client.tenant_id == tenant.id, Client.lead_status == LeadStatus.caliente).scalar() or 0
    total_messages = db.query(func.count(ConversationMessage.id)).filter(ConversationMessage.tenant_id == tenant.id).scalar() or 0
    ai_messages = db.query(func.count(ConversationMessage.id)).filter(ConversationMessage.tenant_id == tenant.id, ConversationMessage.ai_used.is_(True)).scalar() or 0
    return DashboardMetrics(
        total_clients=total_clients,
        cold_leads=cold_leads,
        warm_leads=warm_leads,
        hot_leads=hot_leads,
        total_messages=total_messages,
        ai_messages=ai_messages,
    )
