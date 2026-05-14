@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=python"
where python >nul 2>nul || set "PYTHON_EXE=py -3"
if not exist ".venv\Scripts\python.exe" (
  %PYTHON_EXE% -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [FoxFunkin] Building tools EXE...
pyinstaller --noconfirm --clean --onefile --windowed --name FoxFunkinTools run_tools.py

if not exist "dist\mods" mkdir "dist\mods"
if not exist "dist\data" mkdir "dist\data"
echo Built: dist\FoxFunkinTools.exe
pause
