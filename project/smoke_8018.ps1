$ErrorActionPreference = "Stop"
$jobName = "uvicorn8018"
$existing = Get-Job -Name $jobName -ErrorAction SilentlyContinue
if ($existing) {
  Stop-Job -Job $existing -ErrorAction SilentlyContinue
  Remove-Job -Job $existing -Force -ErrorAction SilentlyContinue
}
$job = Start-Job -Name $jobName -ScriptBlock {
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

  $headers = @{ "X-Tenant-Slug" = "asesor_ai_prod" }

  $body1 = @{ message = "hola quiero informacion" } | ConvertTo-Json -Compress
  $res1 = Invoke-WebRequest -Method Post -Uri "http://127.0.0.1:8018/api/v1/simulate" -Headers $headers -ContentType "application/json" -Body $body1 -UseBasicParsing -TimeoutSec 30
  $json1 = $res1.Content | ConvertFrom-Json
  $reply1 = ([string]$json1.reply).Trim() -replace "`r?`n", " "

  $body2 = @{ message = "quiero empezar" } | ConvertTo-Json -Compress
  $res2 = Invoke-WebRequest -Method Post -Uri "http://127.0.0.1:8018/api/v1/simulate" -Headers $headers -ContentType "application/json" -Body $body2 -UseBasicParsing -TimeoutSec 30
  $json2 = $res2.Content | ConvertFrom-Json
  $reply2 = ([string]$json2.reply).Trim() -replace "`r?`n", " "

  Write-Output "CASE=hola quiero informacion"
  Write-Output "REPLY=$reply1"
  Write-Output "CASE=quiero empezar"
  Write-Output "REPLY=$reply2"
}
finally {
  Stop-Job -Name $jobName -ErrorAction SilentlyContinue
  Remove-Job -Name $jobName -Force -ErrorAction SilentlyContinue
}
