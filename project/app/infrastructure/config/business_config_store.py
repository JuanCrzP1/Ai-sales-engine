"""Lectura y validación de la configuración de cada negocio según el contrato global.

Cada negocio tiene en su carpeta de tenant un documento comercial (`business-config.json`) y, aparte,
sus ajustes técnicos (`engine-settings.json`, opcional).
"""
from __future__ import annotations

import json
from pathlib import Path

from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.engine_settings import EngineSettings
from app.domain.business_config.errors import BusinessConfigError
from app.domain.business_config.validation import validate_document, validate_engine_settings

CONTRACT_FILENAME = "business-config.json"
ENGINE_SETTINGS_FILENAME = "engine-settings.json"


class BusinessConfigStore:
    def __init__(self, tenants_root: Path) -> None:
        self.tenants_root = Path(tenants_root)

    def path_for(self, tenant_slug: str) -> Path:
        return self.tenants_root / tenant_slug / CONTRACT_FILENAME

    def engine_settings_path_for(self, tenant_slug: str) -> Path:
        return self.tenants_root / tenant_slug / ENGINE_SETTINGS_FILENAME

    def exists(self, tenant_slug: str) -> bool:
        return self.path_for(tenant_slug).is_file()

    def load(self, tenant_slug: str) -> BusinessConfig:
        path = self.path_for(tenant_slug)
        if not path.is_file():
            raise BusinessConfigError(f"{tenant_slug}: no existe {CONTRACT_FILENAME}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BusinessConfigError(f"{tenant_slug}: {CONTRACT_FILENAME} no es JSON válido ({exc})") from exc
        return validate_document(tenant_slug, payload).with_engine_settings(self.load_engine_settings(tenant_slug))

    def load_engine_settings(self, tenant_slug: str) -> EngineSettings | None:
        """Ajustes técnicos del negocio; None si no tiene (el motor usa sus valores por defecto)."""
        path = self.engine_settings_path_for(tenant_slug)
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BusinessConfigError(f"{tenant_slug}: {ENGINE_SETTINGS_FILENAME} no es válido ({type(exc).__name__})") from exc
        return validate_engine_settings(tenant_slug, payload)

    @staticmethod
    def dump(config: BusinessConfig | EngineSettings) -> str:
        return json.dumps(config.model_dump(mode="json", exclude_none=True), indent=2, ensure_ascii=False) + "\n"
