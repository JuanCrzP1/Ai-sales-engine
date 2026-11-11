"""Rutas que publica el motor: solo lo que necesitan los canales.

La API de administración del sistema de cuentas anterior (`/auth`, `/clients`, `/conversations`, `/bot-config`, `/connectors`,
`/dashboard`) se retiró el 11 de noviembre de 2026: el panel usa su propia API (`app.admin_api`), y `/auth/register` guardaba
negocios y usuarios sin autenticación. Ya no existe en ningún entorno.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.api import routes
from app.config import settings

PROJECT_DIR = Path(__file__).resolve().parents[1] / "project"
LEGACY_PREFIXES = ("/auth", "/clients", "/conversations", "/bot-config", "/connectors", "/dashboard")
RETIRED_FILES = [
    *(f"app/api/controllers/{name}.py" for name in ("auth", "bot_config", "clientes", "connector_config", "conversaciones", "dashboard")),
    *(f"app/api/schemas/{name}.py" for name in ("auth", "bot_config", "cliente", "connector_config", "conversacion", "dashboard")),
    "app/application/services/crm_service.py",
    "app/connectors/telegram/polling.py",
]


def _paths(monkeypatch, *, mode: str, vercel: bool = False, flag: str | None = None) -> set[str]:
    monkeypatch.setattr(settings, "mode", mode)
    for name, value in (("VERCEL", "1" if vercel else None), ("ENABLE_LEGACY_ADMIN_API", flag)):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    return {route.path for route in routes.build_router().routes}


@pytest.mark.parametrize(
    "mode, vercel, flag",
    [("production", False, None), ("development", True, None), ("development", False, None), ("development", False, "1")],
    ids=["MODE=production", "en_vercel", "en_este_equipo", "con_la_bandera_vieja"],
)
def test_only_what_the_channels_need_is_published_everywhere(monkeypatch, mode, vercel, flag):
    paths = _paths(monkeypatch, mode=mode, vercel=vercel, flag=flag)
    assert sorted(path for path in paths if path.startswith(LEGACY_PREFIXES)) == []
    assert any(path.startswith("/whatsapp") for path in paths)


def test_the_old_admin_api_and_telegram_polling_are_gone():
    assert [name for name in RETIRED_FILES if (PROJECT_DIR / name).exists()] == []


def test_health_does_not_name_any_business():
    from fastapi.testclient import TestClient

    from app.main import app

    response = TestClient(app).get("/health")
    assert (response.status_code, response.json()) == (200, {"status": "ok"})
