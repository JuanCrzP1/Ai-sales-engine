from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_tenant, get_current_user
from app.api.schemas.cliente import ClientCreate, ClientOut
from app.database.connection import get_db
from app.models import AdminUser, Client, Tenant
from app.application.services.crm_service import CRMService

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("/", response_model=ClientOut)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Crea o reutiliza un cliente del tenant y devuelve su código visible `client_code`."""
    crm_service = CRMService(db)
    return crm_service.get_or_create_client(tenant_id=tenant.id, phone_number=payload.phone_number, name=payload.name)


@router.get("/", response_model=list[ClientOut])
def list_clients(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Lista clientes del tenant incluyendo `client_code` para operación y CRM."""
    return db.query(Client).filter(Client.tenant_id == tenant.id).order_by(Client.last_contact_at.desc()).all()
