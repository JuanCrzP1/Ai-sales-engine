from types import SimpleNamespace

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import ACTIVE_TENANT_SLUG
from app.database.connection import get_db
from app.infrastructure.db.repository import DBRepository
from app.models import AdminUser, Tenant
from app.services.auth_service import AuthService
from app.utils.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def resolve_tenant_slug(x_tenant_slug: str | None) -> str:
    tenant_id = str(x_tenant_slug or '').strip()
    if tenant_id == 'asesor_ia_comercial':
        tenant_id = ACTIVE_TENANT_SLUG
    if not tenant_id:
        tenant_id = ACTIVE_TENANT_SLUG
    print("TENANT RECIBIDO:", tenant_id)
    logger.info('TENANT RECIBIDO: %s', tenant_id)
    logger.info('tenant_resolved', extra={'event': 'tenant_resolved', 'tenant_id': tenant_id})
    return tenant_id


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> AdminUser:
    auth_service = AuthService(db)
    user = auth_service.get_user_from_token(token)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return user


def get_current_tenant(
    x_tenant_slug: str | None = Header(default=None, alias="X-Tenant-Slug"),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    resolved_header = resolve_tenant_slug(x_tenant_slug) if x_tenant_slug is not None else None
    if resolved_header and tenant and tenant.slug != resolved_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant no autorizado")
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    logger.info('tenant_resolved', extra={'event': 'tenant_resolved', 'tenant_id': tenant.slug, 'tenant_db_id': tenant.id})
    return tenant


def get_tenant_by_slug_public(x_tenant_slug: str = Header(..., alias="X-Tenant-Slug")) -> Tenant:
    repo = DBRepository()
    tenant = repo.get_tenant_by_slug(resolve_tenant_slug(x_tenant_slug))
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    logger.info('tenant_resolved', extra={'event': 'tenant_resolved', 'tenant_id': tenant.get('slug'), 'tenant_db_id': tenant.get('id')})
    return SimpleNamespace(**tenant)
