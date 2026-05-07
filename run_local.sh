#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/project"

# -------------------------
# Activar entorno virtual
# -------------------------
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "../.venv/bin/activate" ]; then
    source ../.venv/bin/activate
else
    echo "[ERROR] No se pudo encontrar el entorno virtual."
    exit 1
fi

# -------------------------
# NGROK (puerto 8082)
# -------------------------
echo "[INFO] Iniciando ngrok en puerto 8082..."
ngrok http 8082 &

# -------------------------
# TELEGRAM
# -------------------------
TELEGRAM_POLLING_ENABLED=""

if [ -n "$TELEGRAM_TOKEN" ]; then
    TELEGRAM_POLLING_ENABLED=1
elif [ -f "../.env" ] && grep -q "^TELEGRAM_TOKEN=" "../.env"; then
    TELEGRAM_POLLING_ENABLED=1
elif [ -f ".env" ] && grep -q "^TELEGRAM_TOKEN=" ".env"; then
    TELEGRAM_POLLING_ENABLED=1
fi

if [ -n "$TELEGRAM_POLLING_ENABLED" ]; then
    echo "[INFO] Iniciando Telegram polling..."
    python -m app.connectors.telegram.polling &
else
    echo "[INFO] TELEGRAM_TOKEN no definido. Telegram polling no se inicia."
fi

# -------------------------
# BACKEND (puerto 8082)
# -------------------------
echo "[INFO] Iniciando backend en puerto 8082..."
uvicorn app.main:app --reload --port 8082
