"""La configuración del simulador. Solo para desarrollo: se niega a arrancar en producción o en Vercel.

| Variable | Por defecto | Para qué |
|---|---|---|
| `SIM_PORT` | `3300` (Auream usa el 3200) | Puerto del simulador y del teléfono de prueba. |
| `SIM_ADMIN_TOKEN` | `simulador` | Token de administrador (el de uazapi). Debe coincidir con `WHATSAPP_SIMULATOR_TOKEN` del panel. |
| `SIM_DATA_DIR` | `.wa-sim` (en la raíz del repositorio) | Estado (`state.json`) del simulador. Ignorado por git. |
| `SIM_RECEIPT_SECONDS` | `0.7` | Cuánto tarda en llegar el «entregado» (✓✓) de lo que envía el negocio. |
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


class ProductionRefused(RuntimeError):
    """El simulador nunca corre en producción."""


@dataclass(frozen=True)
class SimConfig:
    port: int = 3300
    admin_token: str = "simulador"
    data_dir: Path = REPO_ROOT / ".wa-sim"
    receipt_seconds: float = 0.7


def is_production(env: dict[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return bool(values.get("VERCEL")) or any(str(values.get(name) or "").strip().lower() == "production" for name in ("ENV", "APP_ENV", "ENVIRONMENT"))


def load_config(env: dict[str, str] | None = None) -> SimConfig:
    values = os.environ if env is None else env
    if is_production(values):
        raise ProductionRefused("El simulador de WhatsApp es solo para desarrollo: no arranca en producción ni en Vercel.")
    return SimConfig(
        port=int(values.get("SIM_PORT") or 3300),
        admin_token=str(values.get("SIM_ADMIN_TOKEN") or "simulador"),
        data_dir=Path(values.get("SIM_DATA_DIR") or REPO_ROOT / ".wa-sim"),
        receipt_seconds=float(values.get("SIM_RECEIPT_SECONDS") or 0.7),
    )
