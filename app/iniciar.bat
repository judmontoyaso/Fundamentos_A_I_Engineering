@echo off
REM Arranca backend y frontend, cada uno en su propia ventana.
cd /d "%~dp0"
start "Curso - API (8000)" cmd /k "backend\iniciar-backend.bat"
start "Curso - Frontend (5173)" cmd /k "frontend\iniciar-frontend.bat"
timeout /t 6 >nul
start "" "http://127.0.0.1:5173"
