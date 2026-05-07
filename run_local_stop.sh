#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$SCRIPT_DIR/.run_local"
APP_PORT=8082

kill_if_exists() {
    local name="$1"
    local pid_file="$RUNTIME_DIR/${name}.pid"
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "[INFO] Matando $name (PID $pid)"
            kill "$pid" || true
        else
            echo "[INFO] $name (PID $pid) ya no está corriendo."
        fi
        rm -f "$pid_file"
    else
        echo "[INFO] No hay PID file para $name."
    fi
}

kill_matching_processes() {
    local label="$1"
    local pattern="$2"
    local pids

    pids=$(pgrep -f "$pattern" || true)
    if [ -n "$pids" ]; then
        echo "[INFO] Matando procesos de $label: $pids"
        while IFS= read -r pid; do
            [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
        done <<< "$pids"
    fi
}

kill_port_listener() {
    local port="$1"
    local pids

    pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN || true)
    if [ -n "$pids" ]; then
        echo "[INFO] Matando procesos que escuchan en el puerto $port: $pids"
        while IFS= read -r pid; do
            [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
        done <<< "$pids"
    fi
}

kill_if_exists "ngrok"
kill_if_exists "telegram-polling"
kill_matching_processes "ngrok" "ngrok http $APP_PORT"
kill_matching_processes "telegram-polling" "app.connectors.telegram.polling"
kill_matching_processes "uvicorn" "uvicorn app.main:app --reload --port $APP_PORT"
kill_port_listener "$APP_PORT"

echo "[INFO] Procesos ngrok, telegram-polling y backend detenidos (si estaban activos)."
