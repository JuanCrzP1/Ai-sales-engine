import base64
import hashlib
import hmac
import importlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings
from app.models import AdminUser


Session = Any


def _jwt_module():
    return importlib.import_module('jose.jwt')


def _jwt_error_type():
    return importlib.import_module('jose').JWTError


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
        return f"pbkdf2_sha256${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        try:
            algorithm, salt_b64, digest_b64 = password_hash.split("$", 2)
            if algorithm != "pbkdf2_sha256":
                return False
            salt = base64.b64decode(salt_b64.encode())
            expected = base64.b64decode(digest_b64.encode())
            candidate = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 120000)
            return hmac.compare_digest(candidate, expected)
        except ValueError:
            return False

    def authenticate(self, email: str, password: str) -> AdminUser | None:
        user = self.db.query(AdminUser).filter(AdminUser.email == email).first()
        if not user or not self.verify_password(password, user.password_hash):
            return None
        return user

    def create_access_token(self, user: AdminUser) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        payload = {"sub": str(user.id), "tenant_id": user.tenant_id, "exp": expires_at}
        return _jwt_module().encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def get_user_from_token(self, token: str) -> AdminUser | None:
        try:
            payload = _jwt_module().decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            user_id = int(payload.get("sub"))
        except (_jwt_error_type(), TypeError, ValueError):
            return None
        return self.db.query(AdminUser).filter(AdminUser.id == user_id).first()
