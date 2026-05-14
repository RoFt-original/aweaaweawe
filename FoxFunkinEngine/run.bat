@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=python"
where python >nul 2>nul || set "PYTHON_EXE=py -3"
if not exist ".venv\Scripts\python.exe" (
  echo [FoxFunkin] Creating Python venv...
  %PYTHON_EXE% -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run_engine.py
pause
