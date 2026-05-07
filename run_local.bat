@echo off
setlocal

cd /d %~dp0project

:: Activar entorno virtual
if exist .venv\Scripts\activate (
	call .venv\Scripts\activate
) else (
	call ..\.venv\Scripts\activate
)
if errorlevel 1 (
	echo [ERROR] No se pudo activar el entorno virtual.
	exit /b 1
)

:: -------------------------
:: NGROK (puerto 8082)
:: -------------------------
echo [INFO] Iniciando ngrok en puerto 8082...
start "ngrok" cmd /k ngrok http 8082

:: -------------------------
:: TELEGRAM (NO TOCAR)
:: -------------------------
set TELEGRAM_POLLING_ENABLED=
if defined TELEGRAM_TOKEN set TELEGRAM_POLLING_ENABLED=1
if not defined TELEGRAM_POLLING_ENABLED if exist ..\.env (
	findstr /b /c:"TELEGRAM_TOKEN=" ..\.env >nul && set TELEGRAM_POLLING_ENABLED=1
)
if not defined TELEGRAM_POLLING_ENABLED if exist .env (
	findstr /b /c:"TELEGRAM_TOKEN=" .env >nul && set TELEGRAM_POLLING_ENABLED=1
)

if defined TELEGRAM_POLLING_ENABLED (
	echo [INFO] Iniciando Telegram polling...
	start "telegram-polling" cmd /k python -m app.connectors.telegram.polling
) else (
	echo [INFO] TELEGRAM_TOKEN no definido. Telegram polling no se inicia.
)

:: -------------------------
:: BACKEND (puerto 8082)
:: -------------------------
echo [INFO] Iniciando backend en puerto 8082...
uvicorn app.main:app --reload --port 8082

endlocal
