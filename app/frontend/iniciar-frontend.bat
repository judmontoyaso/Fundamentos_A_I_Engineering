@echo off
REM Frontend del curso (Vite + React) en http://127.0.0.1:5173
cd /d "%~dp0"
if not exist "node_modules\" (
  echo Instalando dependencias del frontend...
  call npm install
)
call npm run dev
pause
