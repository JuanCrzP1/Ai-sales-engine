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
:: PANEL WEB (API en 8010, interfaz en ADMIN_WEB_PORT)
:: -------------------------
set ADMIN_WEB_DIR=%~dp0apps\admin-web
set ADMIN_WEB_PORT=5180
rem Abrir la direccion del motor lleva a este panel, no al de la nube.
if not defined PANEL_URL set "PANEL_URL=http://localhost:%ADMIN_WEB_PORT%"
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
	echo [INFO] Iniciando la API del panel en http://127.0.0.1:8010 ...
	start "admin-api" cmd /k python "%~dp0scripts\run_admin_api.py"
	python "%~dp0scripts\run_admin_api.py" --wait
	if errorlevel 1 (
		echo [AVISO] La API del panel no respondio. Revisa la ventana admin-api. El panel web no se inicia.
	) else (
		echo [INFO] Iniciando panel web en http://localhost:%ADMIN_WEB_PORT% ...
		start "admin-web" cmd /k "cd /d "%ADMIN_WEB_DIR%" && npm run dev -- --port %ADMIN_WEB_PORT% --strictPort --open"
	)
)

:: -------------------------
:: BACKEND (puerto 8082)
:: -------------------------
echo [INFO] Iniciando backend en puerto 8082...
uvicorn app.main:app --reload --port 8082

endlocal
