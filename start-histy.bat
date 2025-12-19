@echo off
setlocal

set ROOT=%~dp0
cd /d "%ROOT%histy-server"

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt

if not defined HISTY_DB_PATH (
  set HISTY_DB_PATH=%ROOT%histy.db
)

echo Starting histy server on http://127.0.0.1:8000
uvicorn app.main:app --reload --port 8000
