#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/project"

PROJECT_DIR="$PWD"
RUNTIME_DIR="$SCRIPT_DIR/.run_local"
APP_PORT=8082

# -------------------------
# Activar entorno virtual
# -------------------------
if [ -f ".venv/bin/activate" ]; then
    VENV_ACTIVATE="$PROJECT_DIR/.venv/bin/activate"
elif [ -f "../.venv/bin/activate" ]; then
    VENV_ACTIVATE="$SCRIPT_DIR/.venv/bin/activate"
else
    echo "[ERROR] No se pudo encontrar el entorno virtual."
    exit 1
fi

source "$VENV_ACTIVATE"

mkdir -p "$RUNTIME_DIR"

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
    start_background_process "telegram-polling" "source \"$VENV_ACTIVATE\" && python -m app.connectors.telegram.polling"
else
    echo "[INFO] TELEGRAM_TOKEN no definido. Telegram polling no se inicia."
fi

# -------------------------
# BACKEND (puerto 8082)
# -------------------------
echo "[INFO] Iniciando backend en puerto 8082..."
uvicorn app.main:app --reload --port "$APP_PORT"
