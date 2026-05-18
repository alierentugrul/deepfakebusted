@echo off
setlocal

set "PROJECT_DIR=%~dp0"

taskkill /FI "WINDOWTITLE eq DeepFakeBusted API*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq DeepFakeBusted Frontend*" /T /F >nul 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$byPort = Get-NetTCPConnection -LocalPort 5000,5173 -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 0 } | Select-Object -ExpandProperty OwningProcess;" ^
  "$pids = @($byPort) | Sort-Object -Unique;" ^
  "if ($pids.Count -eq 0) { Write-Host 'Calisan DeepFakeBusted API/frontend sureci bulunamadi.'; exit 0 };" ^
  "foreach ($id in $pids) { Write-Host ('Kapatiliyor PID=' + $id); Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }"

pause
