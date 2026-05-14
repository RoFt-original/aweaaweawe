@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: import_assets.bat ^<path-to-funkin.assets^>
  pause
  exit /b 1
)
set "PYTHON_EXE=python"
where python >nul 2>nul || set "PYTHON_EXE=py -3"
if not exist ".venv\Scripts\python.exe" (
  echo [FoxFunkin] Creating Python venv...
  %PYTHON_EXE% -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
python -m foxfunkin.tools.import_assets "%~1"
pause
