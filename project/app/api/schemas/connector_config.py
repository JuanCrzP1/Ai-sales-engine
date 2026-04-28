from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConnectorConfigUpdate(BaseModel):
    enabled: bool = True
    use_global_fallback: bool = True
    public_config: dict[str, Any] = Field(default_factory=dict)
    secret_config: dict[str, Any] | None = None


class ConnectorConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    tenant_id: int
    channel: str
    provider: str
    enabled: bool
    use_global_fallback: bool
    public_config: dict[str, Any]
    secret_keys: list[str]
    masked_secret_config: dict[str, str]
    has_tenant_secrets: bool
    effective_source: str
    is_resolved: bool
    updated_at: datetime | None = None