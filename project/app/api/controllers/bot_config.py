from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_tenant, get_current_user
from app.api.schemas.bot_config import BotConfigOut, BotConfigUpdate
from app.database.connection import get_db
from app.models import AdminUser, BotConfig, Tenant

router = APIRouter(prefix="/bot-config", tags=["BotConfig"])


@router.get("/", response_model=BotConfigOut)
def get_bot_config(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    return db.query(BotConfig).filter(BotConfig.tenant_id == tenant.id).first()


@router.put("/", response_model=BotConfigOut)
def update_bot_config(
    payload: BotConfigUpdate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    config = db.query(BotConfig).filter(BotConfig.tenant_id == tenant.id).first()
    for field, value in payload.model_dump().items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config
