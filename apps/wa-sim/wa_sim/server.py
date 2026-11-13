"""Arma el simulador: el uazapi falso (para el motor y el panel), el teléfono de prueba (para hacer de cliente) y su página."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from wa_sim.config import SimConfig
from wa_sim.core.simulator import Simulator
from wa_sim.core.store import SimulatorStore
from wa_sim.phone.api import build_router as build_phone_router
from wa_sim.provider.api import build_router as build_provider_router
from wa_sim.webhooks.notifier import ActivityLog, UazapiNotifier
from wa_sim.webhooks.qr import QR_DATA

UI_DIR = Path(__file__).resolve().parent / "phone" / "ui"


@dataclass
class SimulatorApp:
    app: FastAPI
    simulator: Simulator
    log: ActivityLog


def create_simulator(config: SimConfig, *, persist: bool = True, webhook_transport: httpx.BaseTransport | None = None) -> SimulatorApp:
    """`persist=False` lo deja todo en memoria (las pruebas). `webhook_transport` cambia cómo salen los avisos (pruebas)."""
    holder: dict[str, SimulatorStore] = {"store": SimulatorStore(config.data_dir if persist else None)}
    log = ActivityLog()
    notifier = UazapiNotifier(log, lambda phone: _client_name(holder["store"], phone), transport=webhook_transport)
    simulator = Simulator(holder["store"], notifier, receipt_seconds=config.receipt_seconds)

    app = FastAPI(title="WhatsApp simulado", docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(build_provider_router(simulator, config.admin_token, log))
    app.include_router(build_phone_router(simulator, log, holder["store"].reset))

    @app.get("/")
    def phone_page() -> FileResponse:
        return FileResponse(UI_DIR / "index.html")

    @app.get("/qr.png")
    def qr_image() -> Response:
        return Response(base64.b64decode(QR_DATA), media_type="image/png")

    @app.middleware("http")
    async def never_cached(request, call_next):
        # Es una herramienta en desarrollo: la página y sus archivos siempre se piden de nuevo, así un cambio se ve al recargar.
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")
    return SimulatorApp(app, simulator, log)


def _client_name(store: SimulatorStore, phone: str) -> str:
    client = store.state.clients.get(phone)
    return client.name if client else ""
