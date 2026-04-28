from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    tenant_name: str
    tenant_slug: str
    full_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_slug: str
