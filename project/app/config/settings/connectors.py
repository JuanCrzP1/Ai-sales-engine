from __future__ import annotations

from typing import Any, Dict


CORE_CONNECTOR_KEYS = (
    "database_url",
    "public_base_url",
)


def apply_connectors_section(cfg: Dict[str, Any], raw_cfg: Dict[str, Any] | None) -> None:
    source = raw_cfg if isinstance(raw_cfg, dict) else {}
    for key in CORE_CONNECTOR_KEYS:
        if key in source:
            cfg[key] = source[key]
