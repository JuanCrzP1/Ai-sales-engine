from __future__ import annotations

import json
from base64 import urlsafe_b64encode
from hashlib import sha256
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import SessionLocal
from app.models import Tenant, TenantConnectorConfig
from app.repositories import TenantConnectorRepository


class TenantConnectorService:
    REQUIRED_FIELDS: dict[tuple[str, str], tuple[str, ...]] = {
        ("whatsapp", "twilio"): ("account_sid", "auth_token", "whatsapp_number"),
        ("whatsapp", "meta"): ("access_token", "phone_number_id"),
    }

    PROVIDER_PRIORITY: dict[str, tuple[str, ...]] = {
        "whatsapp": ("twilio", "meta"),
    }

    def __init__(self, db: Session):
        self.db = db
        self.repository = TenantConnectorRepository(db)
        self._fernet = self._build_fernet()

    @staticmethod
    def _build_fernet() -> Fernet:
        seed = (settings.connector_secrets_key or settings.jwt_secret or "change-me-in-production").encode("utf-8")
        return Fernet(urlsafe_b64encode(sha256(seed).digest()))

    @staticmethod
    def _clean_mapping(values: dict[str, Any] | None) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for key, value in (values or {}).items():
            if key is None:
                continue
            normalized_key = str(key).strip()
            if not normalized_key:
                continue
            if value is None:
                continue
            if isinstance(value, str):
                stripped = value.strip()
                if not stripped:
                    continue
                cleaned[normalized_key] = stripped
            else:
                cleaned[normalized_key] = value
        return cleaned

    @staticmethod
    def _merge_mapping(current: dict[str, Any], updates: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(current or {})
        for key, value in (updates or {}).items():
            normalized_key = str(key).strip()
            if not normalized_key:
                continue
            if value is None or (isinstance(value, str) and not value.strip()):
                merged.pop(normalized_key, None)
                continue
            merged[normalized_key] = value.strip() if isinstance(value, str) else value
        return merged

    def _encrypt(self, secret_config: dict[str, Any]) -> str | None:
        payload = self._clean_mapping(secret_config)
        if not payload:
            return None
        token = self._fernet.encrypt(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return token.decode("utf-8")

    def _decrypt(self, encrypted_value: str | None) -> dict[str, Any]:
        if not encrypted_value:
            return {}
        try:
            raw = self._fernet.decrypt(encrypted_value.encode("utf-8"))
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except (InvalidToken, ValueError, TypeError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _load_public_config(record: TenantConnectorConfig | None) -> dict[str, Any]:
        if record is None or not record.public_config_json:
            return {}
        try:
            data = json.loads(record.public_config_json)
            return data if isinstance(data, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _mask_value(value: Any) -> str:
        text = str(value)
        if len(text) <= 4:
            return "***"
        return f"***{text[-4:]}"

    def _mask_secret_config(self, secret_config: dict[str, Any]) -> dict[str, str]:
        return {key: self._mask_value(value) for key, value in secret_config.items()}

    @staticmethod
    def _get_global_settings(channel: str, provider: str) -> dict[str, Any]:
        channel = (channel or "").strip().lower()
        provider = (provider or "").strip().lower()
        global_map = {
            ("whatsapp", "twilio"): {
                "account_sid": settings.twilio_account_sid,
                "auth_token": settings.twilio_auth_token,
                "whatsapp_number": settings.twilio_whatsapp_number,
                "public_base_url": settings.public_base_url,
            },
            ("whatsapp", "meta"): {
                "access_token": settings.meta_access_token,
                "phone_number_id": settings.meta_phone_number_id,
                "verify_token": settings.meta_verify_token,
                "app_secret": settings.meta_app_secret,
                "business_account_id": settings.meta_business_account_id,
            },
        }
        return TenantConnectorService._clean_mapping(global_map.get((channel, provider), {}))

    def _serialize_record(self, record: TenantConnectorConfig, *, include_effective_source: bool = True) -> dict[str, Any]:
        public_config = self._load_public_config(record)
        secret_config = self._decrypt(record.secret_config_encrypted)
        payload = {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "channel": record.channel,
            "provider": record.provider,
            "enabled": record.is_enabled,
            "use_global_fallback": record.use_global_fallback,
            "public_config": public_config,
            "secret_keys": sorted(secret_config.keys()),
            "masked_secret_config": self._mask_secret_config(secret_config),
            "has_tenant_secrets": bool(secret_config),
            "updated_at": record.updated_at,
        }
        if include_effective_source:
            resolved = self.resolve_settings(record.tenant_id, record.channel, record.provider)
            payload["effective_source"] = resolved.get("_source", "none")
            payload["is_resolved"] = bool(resolved.get("_configured"))
        return payload

    def list_connectors(self, tenant_id: int) -> list[dict[str, Any]]:
        return [self._serialize_record(record) for record in self.repository.list_by_tenant(tenant_id)]

    def get_connector(self, tenant_id: int, channel: str, provider: str) -> dict[str, Any] | None:
        record = self.repository.get_by_tenant_channel_provider(tenant_id, channel, provider)
        if record is None:
            resolved = self.resolve_settings(tenant_id, channel, provider)
            if not resolved:
                return None
            return {
                "id": None,
                "tenant_id": tenant_id,
                "channel": channel,
                "provider": provider,
                "enabled": True,
                "use_global_fallback": True,
                "public_config": {},
                "secret_keys": sorted(key for key in resolved.keys() if not key.startswith("_")),
                "masked_secret_config": {},
                "has_tenant_secrets": False,
                "updated_at": None,
                "effective_source": resolved.get("_source", "global"),
                "is_resolved": bool(resolved.get("_configured")),
            }
        return self._serialize_record(record)

    def upsert_connector(
        self,
        tenant_id: int,
        channel: str,
        provider: str,
        *,
        enabled: bool,
        use_global_fallback: bool,
        public_config: dict[str, Any] | None,
        secret_config: dict[str, Any] | None,
    ) -> dict[str, Any]:
        normalized_channel = (channel or "").strip().lower()
        normalized_provider = (provider or "").strip().lower()
        record = self.repository.get_by_tenant_channel_provider(tenant_id, normalized_channel, normalized_provider)

        current_public = self._load_public_config(record)
        current_secret = self._decrypt(record.secret_config_encrypted if record else None)
        merged_public = self._merge_mapping(current_public, public_config)
        merged_secret = current_secret if secret_config is None else self._merge_mapping(current_secret, secret_config)

        if record is None:
            record = TenantConnectorConfig(
                tenant_id=tenant_id,
                channel=normalized_channel,
                provider=normalized_provider,
            )

        record.is_enabled = enabled
        record.use_global_fallback = use_global_fallback
        record.public_config_json = json.dumps(merged_public, ensure_ascii=False) if merged_public else None
        record.secret_config_encrypted = self._encrypt(merged_secret)
        return self._serialize_record(self.repository.save(record), include_effective_source=True)

    def resolve_settings(self, tenant: Tenant | int | None, channel: str, provider: str) -> dict[str, Any]:
        tenant_id = tenant.id if isinstance(tenant, Tenant) else tenant
        normalized_channel = (channel or "").strip().lower()
        normalized_provider = (provider or "").strip().lower()
        record = None
        if tenant_id is not None:
            record = self.repository.get_by_tenant_channel_provider(tenant_id, normalized_channel, normalized_provider)

        tenant_values: dict[str, Any] = {}
        if record is not None and record.is_enabled:
            tenant_values = self._clean_mapping(
                {
                    **self._load_public_config(record),
                    **self._decrypt(record.secret_config_encrypted),
                }
            )

        global_values = self._get_global_settings(normalized_channel, normalized_provider)

        if record is not None and not record.is_enabled:
            resolved = dict(tenant_values)
            resolved["_source"] = "disabled"
            resolved["_configured"] = False
            return resolved

        if record is not None and record.use_global_fallback:
            merged = {**global_values, **tenant_values}
            source = "tenant+global" if tenant_values and global_values else ("tenant" if tenant_values else "global")
        elif tenant_values:
            merged = dict(tenant_values)
            source = "tenant"
        else:
            merged = dict(global_values)
            source = "global" if global_values else "none"

        merged["_source"] = source
        merged["_configured"] = self.is_configured_payload(normalized_channel, normalized_provider, merged)
        return merged

    @classmethod
    def is_configured_payload(cls, channel: str, provider: str, payload: dict[str, Any]) -> bool:
        required_fields = cls.REQUIRED_FIELDS.get(((channel or "").strip().lower(), (provider or "").strip().lower()), ())
        return bool(required_fields) and all(bool(payload.get(field)) for field in required_fields)

    def is_configured(self, tenant: Tenant | int | None, channel: str, provider: str) -> bool:
        resolved = self.resolve_settings(tenant, channel, provider)
        return bool(resolved.get("_configured"))

    def resolve_provider(self, tenant: Tenant | int | None, channel: str, preferred_provider: str | None = None) -> str | None:
        normalized_channel = (channel or "").strip().lower()
        candidate_providers = []
        if preferred_provider:
            candidate_providers.append(preferred_provider.strip().lower())
        for provider in self.PROVIDER_PRIORITY.get(normalized_channel, ()): 
            if provider not in candidate_providers:
                candidate_providers.append(provider)
        for provider in candidate_providers:
            resolved = self.resolve_settings(tenant, normalized_channel, provider)
            if resolved.get("_configured") and str(resolved.get("_source", "")).startswith("tenant"):
                return provider
        for provider in candidate_providers:
            if self.is_configured(tenant, normalized_channel, provider):
                return provider
        return None


def resolve_connector_settings_for_tenant(tenant: Tenant | None, channel: str, provider: str) -> dict[str, Any]:
    if tenant is None:
        return TenantConnectorService._get_global_settings(channel, provider)
    db = SessionLocal()
    try:
        return TenantConnectorService(db).resolve_settings(tenant, channel, provider)
    finally:
        db.close()


def resolve_outbound_provider_for_tenant(tenant: Tenant | None, channel: str, preferred_provider: str | None = None) -> str | None:
    if tenant is None:
        return None
    db = SessionLocal()
    try:
        return TenantConnectorService(db).resolve_provider(tenant, channel, preferred_provider)
    finally:
        db.close()


__all__ = [
    "TenantConnectorService",
    "resolve_connector_settings_for_tenant",
    "resolve_outbound_provider_for_tenant",
]