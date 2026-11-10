"""Rutas que publica el motor: en producción, solo lo que necesitan los canales.

Las de administración del sistema de cuentas anterior (`/auth`, `/clients`, `/conversations`, `/bot-config`, `/connectors`,
`/dashboard`) no se publican en producción ni en Vercel: `/auth/register` guardaría negocios y usuarios sin autenticación.
Fuera de producción siguen como estaban (ver `test_simulation_endpoint_security.py`).
"""
from __future__ import annotations

import pytest

from app.api import routes
from app.config import settings

LEGACY_PREFIXES = ("/auth", "/clients", "/conversations", "/bot-config", "/connectors", "/dashboard")


def _paths(monkeypatch, *, mode: str, vercel: bool = False, flag: str | None = None) -> set[str]:
    monkeypatch.setattr(settings, "mode", mode)
    for name, value in (("VERCEL", "1" if vercel else None), ("ENABLE_LEGACY_ADMIN_API", flag)):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    return {route.path for route in routes.build_router().routes}


def _legacy(paths: set[str]) -> list[str]:
    return sorted(path for path in paths if path.startswith(LEGACY_PREFIXES))


@pytest.mark.parametrize("mode, vercel", [("production", False), ("development", True)], ids=["MODE=production", "en_vercel"])
def test_production_only_publishes_what_the_channels_need(monkeypatch, mode, vercel):
    paths = _paths(monkeypatch, mode=mode, vercel=vercel)
    assert _legacy(paths) == []
    assert any(path.startswith("/whatsapp") for path in paths)


def test_health_does_not_name_any_business():
    from fastapi.testclient import TestClient

    from app.main import app

    response = TestClient(app).get("/health")
    assert (response.status_code, response.json()) == (200, {"status": "ok"})


def test_outside_production_the_routes_stay_as_they_were(monkeypatch):
    paths = _paths(monkeypatch, mode="development")
    assert {"/auth/register", "/auth/login"} <= paths
    assert {prefix for prefix in LEGACY_PREFIXES if any(path.startswith(prefix) for path in paths)} == set(LEGACY_PREFIXES)


@pytest.mark.parametrize("flag, published", [("1", True), ("0", False)])
def test_the_flag_decides_explicitly(monkeypatch, flag, published):
    assert bool(_legacy(_paths(monkeypatch, mode="production", flag=flag))) is published
    assert bool(_legacy(_paths(monkeypatch, mode="development", flag=flag))) is published
