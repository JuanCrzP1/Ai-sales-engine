from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_tenant, get_current_user
from app.api.schemas.connector_config import ConnectorConfigOut, ConnectorConfigUpdate
from app.database.connection import get_db
from app.models import AdminUser, Tenant
from app.services.tenant_connector_service import TenantConnectorService

router = APIRouter(prefix="/connectors", tags=["Connectors"])


@router.get("/", response_model=list[ConnectorConfigOut])
def list_connector_configs(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    return TenantConnectorService(db).list_connectors(tenant.id)


@router.get("/{channel}/{provider}", response_model=ConnectorConfigOut)
def get_connector_config(
    channel: str,
    provider: str,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    connector = TenantConnectorService(db).get_connector(tenant.id, channel, provider)
    if connector is None:
        raise HTTPException(status_code=404, detail="Conector no configurado para este tenant.")
    return connector


@router.put("/{channel}/{provider}", response_model=ConnectorConfigOut)
def upsert_connector_config(
    channel: str,
    provider: str,
    payload: ConnectorConfigUpdate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    return TenantConnectorService(db).upsert_connector(
        tenant_id=tenant.id,
        channel=channel,
        provider=provider,
        enabled=payload.enabled,
        use_global_fallback=payload.use_global_fallback,
        public_config=payload.public_config,
        secret_config=payload.secret_config,
    )