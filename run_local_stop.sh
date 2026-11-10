#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$SCRIPT_DIR/.run_local"
APP_PORT=8082
ADMIN_API_PORT=8010
ADMIN_WEB_PORT=5180

# Solo se detiene lo que es de este proyecto: un proceso cuya carpeta de trabajo o cuya orden están dentro del repositorio. Otro
# programa en los mismos puertos o con una orden parecida, como el Vite de otro proyecto, no se toca.
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd -P)"

process_dir() {
    lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1
}

belongs_to_project() {
    case "$(process_dir "$1")" in
        "$PROJECT_ROOT" | "$PROJECT_ROOT"/*) return 0 ;;
    esac
    ps -o command= -p "$1" 2>/dev/null | grep -qF "$PROJECT_ROOT"
}

stop_process() {
    local label="$1"
    local pid="$2"
    if belongs_to_project "$pid"; then
        echo "[INFO] Matando $label (PID $pid)"
        kill "$pid" 2>/dev/null || true
    else
        echo "[AVISO] No se detiene el PID $pid ($label): es de otro programa, en $(process_dir "$pid")."
    fi
}

kill_if_exists() {
    local name="$1"
    local pid_file="$RUNTIME_DIR/${name}.pid"
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            # Tras un reinicio, el número puede ser ya de otro programa.
            stop_process "$name" "$pid"
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
    local pid
    for pid in $(pgrep -f "$pattern" || true); do
        stop_process "$label" "$pid"
    done
}

kill_port_listener() {
    local port="$1"
    local pid
    for pid in $(lsof -tiTCP:"$port" -sTCP:LISTEN || true); do
        stop_process "lo que escucha en el puerto $port" "$pid"
    done
}

# En Windows no hay lsof ni pgrep, y run_local.bat abre una ventana por servicio: se detiene cada ventana con todo lo que
# lanzó, identificándola por su línea de órdenes. Nunca se toca una consola que no sea de estos servicios.
stop_windows_services() {
    powershell.exe -NoProfile -NonInteractive -Command '
        $all = @(Get-CimInstance Win32_Process)
        $services = @(
            @{ Label = "lanzador";          Names = "cmd.exe";                                   Pattern = "*run_local.bat*" },
            @{ Label = "ngrok";             Names = "cmd.exe", "ngrok.exe";                      Pattern = "*ngrok*http*'"$APP_PORT"'*" },
            @{ Label = "telegram-polling";  Names = "cmd.exe", "python.exe";                     Pattern = "*app.connectors.telegram.polling*" },
            @{ Label = "backend";           Names = "uvicorn.exe", "python.exe";                 Pattern = "*uvicorn*app.main:app*--port*'"$APP_PORT"'*" },
            @{ Label = "API del panel";     Names = "cmd.exe", "python.exe";                     Pattern = "*run_admin_api.py*" },
            @{ Label = "panel web";         Names = "cmd.exe", "node.exe";                       Pattern = "*run*dev*--port*'"$ADMIN_WEB_PORT"'*" },
            @{ Label = "panel web";         Names = "cmd.exe", "node.exe";                       Pattern = "*vite*--port*'"$ADMIN_WEB_PORT"'*" }
        )
        $targets = @{}
        foreach ($service in $services) {
            $found = @($all | Where-Object { $service.Names -contains $_.Name -and $_.CommandLine -like $service.Pattern })
            if ($found.Count -gt 0) { Write-Output ("[INFO] Deteniendo " + $service.Label + ": " + (($found | ForEach-Object { $_.ProcessId }) -join " ")) }
            foreach ($process in $found) { $targets[[int]$process.ProcessId] = $true }
        }
        # Cada ventana se lleva lo que lanzó, como el proceso hijo con el que uvicorn recarga el motor.
        do {
            $before = $targets.Count
            foreach ($process in $all) { if ($targets.ContainsKey([int]$process.ParentProcessId)) { $targets[[int]$process.ProcessId] = $true } }
        } while ($targets.Count -gt $before)
        # Un proceso puede haber caído ya junto con su ventana: no es un error de la parada.
        foreach ($id in $targets.Keys) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
        exit 0
    '
}

case "$(uname -s)" in
    MINGW* | MSYS* | CYGWIN*)
        stop_windows_services
        rm -f "$RUNTIME_DIR"/*.pid
        ;;
    *)
        kill_if_exists "ngrok"
        kill_if_exists "telegram-polling"
        kill_if_exists "admin-web"
        kill_if_exists "admin-api"
        kill_port_listener "$ADMIN_WEB_PORT"
        kill_port_listener "$ADMIN_API_PORT"
        kill_matching_processes "ngrok" "ngrok http $APP_PORT"
        kill_matching_processes "telegram-polling" "app.connectors.telegram.polling"
        kill_matching_processes "API del panel" "scripts/run_admin_api.py"
        kill_matching_processes "uvicorn" "uvicorn app.main:app --reload --port $APP_PORT"
        kill_port_listener "$APP_PORT"
        ;;
esac

echo "[INFO] Procesos ngrok, telegram-polling, panel web, API del panel y backend detenidos (si estaban activos)."
