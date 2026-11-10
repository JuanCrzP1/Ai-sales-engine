"""
run_admin_api.py

La API local del panel de administración (`apps/admin-web`) sobre la base local de BusinessConfig. La arrancan los
lanzadores del sistema, `run_local.bat` y `run_local.sh`.

Escucha únicamente en 127.0.0.1: no tiene autenticación y no debe exponerse a otras redes. Crea las tablas si faltan y
no toca lo que la base ya contenga. No lee `.env`.

La clave que cifra los datos de pago se toma de `BUSINESS_CONFIG_SECRETS_KEY`, de `secrets.local.env` (ignorado por git, para
trabajar desde varios equipos: ver `scripts/local_secrets.py`) o del archivo `.ai-sales-engine/business_config_secrets.key` de la
carpeta del usuario, que se crea solo la primera vez y se reutiliza siempre. Conviene guardar una copia: sin esa clave, los datos
de pago no se pueden leer.

Usage:
  python scripts/run_admin_api.py          # arranca la API
  python scripts/run_admin_api.py --wait   # espera a que responda; termina con 1 si no lo hace a tiempo

Variables opcionales: `BUSINESS_CONFIG_SECRETS_KEY`, `AI_SALES_ENGINE_SECRETS_FILE` (otra ubicación de `secrets.local.env`),
`BUSINESS_CONFIG_DATABASE_URL` (otro archivo SQLite) y `ADMIN_API_PORT` (8010 por defecto).
"""
from __future__ import annotations

import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import uvicorn  # noqa: E402

from app.admin_api.main import create_app  # noqa: E402
from app.domain.business_config.errors import SecretResolutionError  # noqa: E402
from app.infrastructure.business_config.database import (  # noqa: E402
    build_assistant_lab_service,
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.payment_secret_store import check_secrets_key  # noqa: E402
from app.infrastructure.business_config.secrets_key import KEY_FILE, ensure_secrets_key  # noqa: E402

# Fijo a propósito, sin opción para cambiarlo: la API no tiene autenticación.
HOST = "127.0.0.1"
WAIT_SECONDS = 30


def _port() -> int:
    return int(os.getenv("ADMIN_API_PORT", "8010"))


def _wait_until_ready(port: int, timeout: float = WAIT_SECONDS) -> int:
    """Para los lanzadores: 0 cuando la API responde; 1 si no lo hace a tiempo, y entonces no se abre la interfaz."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with opener.open(f"http://{HOST}:{port}/api/health", timeout=2) as response:
                if response.status == 200:
                    print(f"[ok] La API del panel responde en http://{HOST}:{port}")
                    return 0
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.5)
    print(f"[error] La API del panel no respondió en {timeout} segundos")
    return 1


def _assistant_lab(engine, service):
    """La inteligencia artificial de cada negocio y su área de pruebas, con el motor real. Se importa aquí, al arrancar: el motor
    trae su configuración (lee el `.env`), pero el área de pruebas solo usa la clave de IA de cada negocio."""
    from app.application.assistant_lab.engine_runner import EngineAssistantRunner
    from app.config import settings
    from app.infrastructure.ai.openrouter_key_verifier import OpenRouterKeyVerifier
    from app.infrastructure.ai.openrouter_models import OpenRouterModelCatalog

    return build_assistant_lab_service(
        engine,
        service,
        verifier=OpenRouterKeyVerifier(),
        runner=EngineAssistantRunner(),
        catalog=OpenRouterModelCatalog(),
        default_model=settings.openrouter_model,
    )


def main() -> int:
    if "--wait" in sys.argv[1:]:
        return _wait_until_ready(_port())
    engine = create_business_config_engine()
    if engine.dialect.name != "sqlite":
        print("[error] la API local solo usa una base SQLite: PostgreSQL pertenece a la fase de nube")
        return 1
    create_local_schema(engine)
    try:
        if ensure_secrets_key(engine):
            print(f"[ok] Clave de cifrado creada en {KEY_FILE}. Guarda una copia fuera de este equipo.")
        check_secrets_key()
    except SecretResolutionError as exc:
        print(f"[error] {exc}")
        return 1
    port = _port()
    print(f"[ok] API del panel en http://{HOST}:{port}")
    service = build_business_config_service(engine)
    from app.infrastructure.business_config.conversation_store import ConversationStore
    from app.infrastructure.business_config.notification_store import NotificationStore
    from app.infrastructure.business_config.usage_store import UsageCounterStore
    from app.config import settings
    from app.infrastructure.business_config.database import build_whatsapp_channel_service
    from app.infrastructure.channels.public_url import engine_public_url, webhook_base
    from app.infrastructure.channels.uazapi import UazapiClient

    if engine_public_url() is None:
        print("[aviso] Sin ENGINE_PUBLIC_URL: WhatsApp se puede conectar, pero los mensajes no llegarán al motor (usa ./run_local.sh, que la toma de ngrok).")
    app = create_app(
        service,
        _assistant_lab(engine, service),
        conversations=ConversationStore(engine),
        notifications=NotificationStore(engine),
        usage=UsageCounterStore(engine),
        whatsapp=build_whatsapp_channel_service(engine, UazapiClient, webhook_base=webhook_base(settings.api_prefix)),
    )
    uvicorn.run(app, host=HOST, port=port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
