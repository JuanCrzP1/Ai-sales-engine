# Prueba de humo de /api/v1/simulate contra un servidor temporal en 127.0.0.1:8018.
# Comprueba que, con la ruta habilitada, una peticion sin token se rechaza con 401.
# No llega al modelo ni consume API. La simulacion con un administrador identificado queda
# pendiente de la autenticacion definitiva, en la fase de nube (ver docs/operations.md).
# La ruta se habilita solo para este servidor, con un secreto temporal generado aqui.
$ErrorActionPreference = "Stop"
$jobName = "uvicorn8018"
$existing = Get-Job -Name $jobName -ErrorAction SilentlyContinue
if ($existing) {
  Stop-Job -Job $existing -ErrorAction SilentlyContinue
  Remove-Job -Job $existing -Force -ErrorAction SilentlyContinue
}
$job = Start-Job -Name $jobName -ScriptBlock {
  $env:ENABLE_SIMULATION_ENDPOINT = "true"
  $env:JWT_SECRET = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
  Set-Location "c:/dev/Ai-sales-engine/project"
  & "c:/dev/Ai-sales-engine/.venv/Scripts/python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8018 --log-level warning
}
try {
  $ready = $false
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  while (-not $ready) {
    try {
      $null = Invoke-WebRequest -Uri "http://127.0.0.1:8018/health" -UseBasicParsing -TimeoutSec 1
      $ready = $true
    } catch {
      if ($sw.Elapsed.TotalSeconds -ge 60) { throw "Server not ready on 8018" }
    }
  }

  $anonymousStatus = 0
  try {
    $body = @{ user_message = "hola" } | ConvertTo-Json -Compress
    $anonymousStatus = (Invoke-WebRequest -Method Post -Uri "http://127.0.0.1:8018/api/v1/simulate" -Headers @{ "X-Tenant-Slug" = "asesor_ai_prod" } -ContentType "application/json" -Body $body -UseBasicParsing -TimeoutSec 30).StatusCode
  } catch {
    $anonymousStatus = [int]$_.Exception.Response.StatusCode
  }
  if ($anonymousStatus -ne 401) { throw "Sin token se esperaba 401 y se recibio $anonymousStatus" }

  Write-Output "CASE=peticion sin token"
  Write-Output "STATUS=$anonymousStatus"
}
finally {
  Stop-Job -Name $jobName -ErrorAction SilentlyContinue
  Remove-Job -Name $jobName -Force -ErrorAction SilentlyContinue
}
