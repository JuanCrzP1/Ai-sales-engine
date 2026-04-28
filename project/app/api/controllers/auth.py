from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.database.connection import get_db
from app.models import AdminUser, BotConfig, Tenant
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(Tenant).filter(Tenant.slug == payload.tenant_slug).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El slug del tenant ya existe")
    if db.query(AdminUser).filter(AdminUser.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya existe")

    tenant = Tenant(name=payload.tenant_name, slug=payload.tenant_slug)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    auth_service = AuthService(db)
    user = AdminUser(
        tenant_id=tenant.id,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=auth_service.hash_password(payload.password),
    )
    db.add(user)
    db.add(BotConfig(tenant_id=tenant.id, company_name=payload.tenant_name, enable_ai_engine=True, enable_optimizer=True))
    db.commit()
    db.refresh(user)

    return TokenResponse(access_token=auth_service.create_access_token(user), tenant_slug=tenant.slug)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    return TokenResponse(access_token=auth_service.create_access_token(user), tenant_slug=tenant.slug)
