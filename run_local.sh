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
    echo "[INFO] Telegram y el backend necesitan PostgreSQL disponible antes de iniciar."
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

# -------------------------
# TELEGRAM
# -------------------------
TELEGRAM_POLLING_ENABLED=""

if [ -n "${TELEGRAM_TOKEN:-}" ]; then
    TELEGRAM_POLLING_ENABLED=1
elif [ -f "../.env" ] && grep -q "^TELEGRAM_TOKEN=" "../.env"; then
    TELEGRAM_POLLING_ENABLED=1
elif [ -f ".env" ] && grep -q "^TELEGRAM_TOKEN=" ".env"; then
    TELEGRAM_POLLING_ENABLED=1
fi

if [ -n "$TELEGRAM_POLLING_ENABLED" ]; then
    echo "[INFO] Iniciando Telegram polling..."
    start_background_process "telegram-polling" "\"$PYTHON_BIN\" -m app.connectors.telegram.polling"
else
    echo "[INFO] TELEGRAM_TOKEN no definido. Telegram polling no se inicia."
fi

# -------------------------
# BACKEND (puerto 8082)
# -------------------------
echo "[INFO] Iniciando backend en puerto 8082..."
"$PYTHON_BIN" -m uvicorn app.main:app --reload --port "$APP_PORT"
