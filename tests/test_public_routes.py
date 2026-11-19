"""Rutas que publica el motor: solo lo que necesitan los canales.

La API de administración del sistema de cuentas anterior (`/auth`, `/clients`, `/conversations`, `/bot-config`, `/connectors`,
`/dashboard`) se retiró el 11 de noviembre de 2026: el panel usa su propia API (`app.admin_api`), y `/auth/register` guardaba
negocios y usuarios sin autenticación. Ya no existe en ningún entorno.

El 18 de noviembre de 2026 se retiró el resto del sistema anterior: el webhook de WhatsApp de Meta (buscaba el negocio en una tabla
que en producción está vacía; WhatsApp llega por código QR), la simulación (`/simulate`, apagada y sin forma de autenticarse) con
su sistema de cuentas, y los modelos, repositorios y conectores que solo ellos usaban.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.api import routes
from app.config import settings

PROJECT_DIR = Path(__file__).resolve().parents[1] / "project"
LEGACY_PREFIXES = ("/auth", "/clients", "/conversations", "/bot-config", "/connectors", "/dashboard", "/simulate", "/whatsapp/webhook")
RETIRED_FILES = [
    *(f"app/api/controllers/{name}.py" for name in ("auth", "bot_config", "clientes", "connector_config", "conversaciones", "dashboard")),
    *(f"app/api/schemas/{name}.py" for name in ("auth", "bot_config", "cliente", "connector_config", "conversacion", "dashboard")),
    "app/application/services/crm_service.py",
    "app/connectors/telegram/polling.py",
    # 18 de noviembre de 2026.
    "app/api/controllers/whatsapp_webhook.py",
    "app/api/controllers/simulation.py",
    "app/api/dependencies.py",
    "app/application/response_guard.py",
    "app/services/auth_service.py",
    "app/services/tenant_channel_resolver.py",
    "app/services/tenant_connector_service.py",
    "app/services/tenant_secrets_service.py",
    "app/connectors",
    "app/models",
    "app/repositories",
    "app/database",
    "app/data",
    "app/utils/helpers.py",
    "app/infrastructure/db/repository.py",
    "app/infrastructure/persistence/client_repository.py",
    "app/infrastructure/config",
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
    assert {"/channels/whatsapp/{webhook_id}", "/assistant/messages"} <= paths


def test_the_previous_system_is_gone():
    assert [name for name in RETIRED_FILES if (PROJECT_DIR / name).exists()] == []


def test_health_does_not_name_any_business():
    from fastapi.testclient import TestClient

    from app.main import app

    response = TestClient(app).get("/health")
    assert (response.status_code, response.json()) == (200, {"status": "ok"})


def test_opening_the_engine_address_leads_to_the_panel(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import PUBLIC_PANEL_URL, app

    client = TestClient(app, follow_redirects=False)
    monkeypatch.delenv("PANEL_URL", raising=False)
    assert (client.get("/").status_code, client.get("/").headers["location"]) == (307, PUBLIC_PANEL_URL)
    monkeypatch.setenv("PANEL_URL", "http://localhost:5180")
    assert client.get("/").headers["location"] == "http://localhost:5180"
