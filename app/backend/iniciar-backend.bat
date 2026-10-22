@echo off
REM API del curso (FastAPI) en http://127.0.0.1:8000
cd /d "%~dp0"
if not exist ".venv\" (
  echo Creando entorno virtual del backend...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)
if not exist ".env" copy ".env.example" ".env" >nul
python run.py
pause
