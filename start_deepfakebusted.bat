@echo off
setlocal

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist "venv\Scripts\python.exe" (
  echo [ERROR] venv\Scripts\python.exe bulunamadi.
  echo Once sanal ortami ve Python bagimliliklarini kurun.
  pause
  exit /b 1
)

if not exist "web\frontend\node_modules\vite\bin\vite.js" (
  echo [ERROR] Frontend bagimliliklari bulunamadi.
  echo Komut: cd web\frontend ^&^& npm install
  pause
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js PATH uzerinde bulunamadi.
  pause
  exit /b 1
)

echo DeepFakeBusted API baslatiliyor...
start "DeepFakeBusted API" cmd /k "cd /d ""%PROJECT_DIR%"" && venv\Scripts\python.exe web\server.py"

echo API hazir olana kadar bekleniyor...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ok = $false;" ^
  "for ($i = 0; $i -lt 60; $i++) {" ^
  "  try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/api/models -TimeoutSec 2 | Out-Null; $ok = $true; break } catch { Start-Sleep -Seconds 2 }" ^
  "};" ^
  "if (-not $ok) { Write-Host '[ERROR] API 120 saniye icinde hazir olmadi.'; exit 1 }"
if errorlevel 1 (
  pause
  exit /b 1
)

echo DeepFakeBusted frontend baslatiliyor...
start "DeepFakeBusted Frontend" cmd /k "cd /d ""%PROJECT_DIR%web\frontend"" && node node_modules\vite\bin\vite.js --host 127.0.0.1 --port 5173"

echo Tarayici aciliyor...
timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:5173/"

echo.
echo API:      http://127.0.0.1:5000
echo Frontend: http://127.0.0.1:5173
pause
