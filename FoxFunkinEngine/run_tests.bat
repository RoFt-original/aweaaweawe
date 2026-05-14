@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=python"
where python >nul 2>nul || set "PYTHON_EXE=py -3"
if not exist ".venv\Scripts\python.exe" (
  %PYTHON_EXE% -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
set SDL_VIDEODRIVER=dummy
set SDL_AUDIODRIVER=dummy
python -m unittest discover -s tests
pause
