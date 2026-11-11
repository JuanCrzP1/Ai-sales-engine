#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/project"

PROJECT_DIR="$PWD"
RUNTIME_DIR="$SCRIPT_DIR/.run_local"
APP_PORT=8082

# -------------------------
# Resolver entorno virtual
# -------------------------
if [ -f ".venv/bin/activate" ]; then
    VENV_DIR="$PROJECT_DIR/.venv"
elif [ -f "../.venv/bin/activate" ]; then
    VENV_DIR="$SCRIPT_DIR/.venv"
else
    echo "[ERROR] No se pudo encontrar el entorno virtual."
    exit 1
fi

PYTHON_BIN="$VENV_DIR/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "[ERROR] No se pudo encontrar el ejecutable de Python en $PYTHON_BIN"
    exit 1
fi

mkdir -p "$RUNTIME_DIR"

check_database_connection() {
    "$PYTHON_BIN" - <<'PY'
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

project_dir = Path.cwd()
workspace_root = project_dir.parent
for candidate in (workspace_root / ".env", project_dir / ".env"):
    if candidate.exists():
        load_dotenv(dotenv_path=candidate, override=False)

database_url = str(os.getenv("DATABASE_URL") or "").strip()
if not database_url:
    print("[ERROR] DATABASE_URL no esta definido.")
    sys.exit(1)

try:
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
except Exception as exc:
    print(f"[ERROR] No se pudo conectar a DATABASE_URL: {exc}")
    sys.exit(1)
PY
}

if ! check_database_connection; then
    echo "[INFO] El backend necesita PostgreSQL disponible antes de iniciar."
    echo "[INFO] Si usas Docker Desktop, abre Docker y luego ejecuta: docker compose up -d db"
    echo "[INFO] Si usas Postgres local, confirma que este escuchando en el puerto configurado por DATABASE_URL."
    exit 1
fi

if lsof -nP -iTCP:"$APP_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "[ERROR] El puerto $APP_PORT ya esta en uso."
    echo "[INFO] Ejecuta ./run_local_stop.sh para cerrar procesos previos antes de volver a iniciar."
    exit 1
fi

start_background_process() {
    local name="$1"
    local command="$2"
    local log_file="$RUNTIME_DIR/${name}.log"
    local pid_file="$RUNTIME_DIR/${name}.pid"

    nohup bash -lc "cd $(printf '%q' "$PROJECT_DIR") && ${command}" >"$log_file" 2>&1 &
    echo $! > "$pid_file"
    echo "[INFO] ${name} iniciado en background. PID $(cat "$pid_file"). Log: $log_file"
}

# -------------------------
# NGROK (puerto 8082)
# -------------------------
if ! command -v ngrok >/dev/null 2>&1; then
    echo "[ERROR] ngrok no esta instalado."
    echo "[INFO] Instala ngrok con: brew install ngrok"
    echo "[INFO] Configura tu token con: ngrok config add-authtoken <tu_token>"
    exit 1
fi

echo "[INFO] Iniciando ngrok en puerto 8082..."
start_background_process "ngrok" "ngrok http $APP_PORT"

# La dirección pública del motor: con ella, la API del panel registra en uazapi el webhook
# de WhatsApp por código QR de cada negocio. Si ya viene definida, se respeta.
ngrok_public_url() {
    "$PYTHON_BIN" - <<'PY'
import json
import time
import urllib.request

for _ in range(20):
    try:
        with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=2) as response:
            tunnels = json.load(response).get("tunnels", [])
        for tunnel in tunnels:
            url = str(tunnel.get("public_url") or "")
            if url.startswith("https://"):
                print(url)
                raise SystemExit(0)
    except (OSError, ValueError):
        pass
    time.sleep(0.5)
raise SystemExit(1)
PY
}

if [ -z "${ENGINE_PUBLIC_URL:-}" ]; then
    if ENGINE_PUBLIC_URL="$(ngrok_public_url)"; then
        export ENGINE_PUBLIC_URL
        echo "[INFO] Dirección pública del motor: $ENGINE_PUBLIC_URL"
    else
        unset ENGINE_PUBLIC_URL
        echo "[AVISO] No se pudo leer la dirección de ngrok. WhatsApp por código QR no recibirá mensajes en este equipo."
    fi
fi

# -------------------------
# PANEL WEB (API en 8010, interfaz en ADMIN_WEB_PORT)
# -------------------------
ADMIN_WEB_DIR="$SCRIPT_DIR/apps/admin-web"
ADMIN_WEB_PORT=5180

if ! command -v npm >/dev/null 2>&1; then
    echo "[AVISO] npm no esta instalado. El panel web no se inicia."
elif [ ! -f "$ADMIN_WEB_DIR/package.json" ]; then
    echo "[AVISO] No se encontro $ADMIN_WEB_DIR. El panel web no se inicia."
elif lsof -nP -iTCP:"$ADMIN_WEB_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "[AVISO] El puerto $ADMIN_WEB_PORT ya esta en uso. El panel web no se inicia."
else
    if [ ! -d "$ADMIN_WEB_DIR/node_modules" ]; then
        echo "[INFO] Instalando dependencias del panel web..."
        (cd "$ADMIN_WEB_DIR" && npm install)
    fi
    echo "[INFO] Iniciando la API del panel en http://127.0.0.1:8010 ..."
    start_background_process "admin-api" "\"$PYTHON_BIN\" \"$SCRIPT_DIR/scripts/run_admin_api.py\""
    if "$PYTHON_BIN" "$SCRIPT_DIR/scripts/run_admin_api.py" --wait; then
        echo "[INFO] Iniciando panel web en http://localhost:$ADMIN_WEB_PORT ..."
        start_background_process "admin-web" "cd $(printf '%q' "$ADMIN_WEB_DIR") && npm run dev -- --port $ADMIN_WEB_PORT --strictPort --open"
    else
        echo "[AVISO] La API del panel no respondio. Revisa $RUNTIME_DIR/admin-api.log. El panel web no se inicia."
    fi
fi

# -------------------------
# BACKEND (puerto 8082)
# -------------------------
echo "[INFO] Iniciando backend en puerto 8082..."
"$PYTHON_BIN" -m uvicorn app.main:app --reload --port "$APP_PORT"
