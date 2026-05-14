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

echo [FoxFunkin] Building engine EXE...
pyinstaller --noconfirm --clean --onefile --windowed --name FoxFunkinEngine run_engine.py

echo [FoxFunkin] Preparing dist folders...
if not exist "dist\data" mkdir "dist\data"
if not exist "dist\mods" mkdir "dist\mods"
copy /Y "README_RU.md" "dist\README_RU.txt" >nul
copy /Y "data\README_PUT_ASSETS_HERE.txt" "dist\data\README_PUT_ASSETS_HERE.txt" >nul
xcopy /E /I /Y "mods\example_10min_mod" "dist\mods\example_10min_mod" >nul

echo.
echo Built: dist\FoxFunkinEngine.exe
echo Put external assets into dist\data\
echo.
pause
