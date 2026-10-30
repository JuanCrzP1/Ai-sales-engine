"""Lectura y validación de la configuración de cada negocio según el contrato global.

Cada negocio tiene un único documento `business-config.json` en su carpeta de tenant.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.domain.business_config.contract import BusinessConfig

CONTRACT_FILENAME = "business-config.json"


class BusinessConfigError(ValueError):
    """La configuración del negocio no existe, no es JSON válido o no cumple el contrato."""


class BusinessConfigStore:
    def __init__(self, tenants_root: Path) -> None:
        self.tenants_root = Path(tenants_root)

    def path_for(self, tenant_slug: str) -> Path:
        return self.tenants_root / tenant_slug / CONTRACT_FILENAME

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
        try:
            config = BusinessConfig.model_validate(payload)
        except ValidationError as exc:
            raise BusinessConfigError(f"{tenant_slug}: la configuración no cumple el contrato ({exc.error_count()} errores)") from exc
        if config.tenant_slug != tenant_slug:
            raise BusinessConfigError(f"{tenant_slug}: el documento declara el tenant '{config.tenant_slug}'")
        return config

    @staticmethod
    def dump(config: BusinessConfig) -> str:
        return json.dumps(config.model_dump(mode="json", exclude_none=True), indent=2, ensure_ascii=False) + "\n"
