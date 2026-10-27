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
:: PANEL WEB (puerto 5173)
:: -------------------------
set ADMIN_WEB_DIR=%~dp0apps\admin-web
where npm >nul 2>nul
if errorlevel 1 (
	echo [AVISO] npm no esta instalado. El panel web no se inicia.
) else if not exist "%ADMIN_WEB_DIR%\package.json" (
	echo [AVISO] No se encontro %ADMIN_WEB_DIR%. El panel web no se inicia.
) else (
	if not exist "%ADMIN_WEB_DIR%\node_modules" (
		echo [INFO] Instalando dependencias del panel web...
		pushd "%ADMIN_WEB_DIR%"
		call npm install
		popd
	)
	echo [INFO] Iniciando panel web en http://localhost:5173 ...
	start "admin-web" cmd /k "cd /d "%ADMIN_WEB_DIR%" && npm run dev -- --port 5173 --strictPort --open"
)

:: -------------------------
:: BACKEND (puerto 8082)
:: -------------------------
echo [INFO] Iniciando backend en puerto 8082...
uvicorn app.main:app --reload --port 8082

endlocal
