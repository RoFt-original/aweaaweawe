@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if "%~1"=="" (
  echo Usage:
  echo   import_assets.bat ^<path-to-fnf-assets-folder^>
  echo.
  echo The path may point to:
  echo   - a folder containing preload, shared, songs, week1, etc.
  echo   - a folder containing an assets subfolder
  echo   - a built FNF folder that contains export\release\...\assets
  echo.
  echo Example:
  echo   import_assets.bat C:\Games\funkin.assets
  echo   import_assets.bat C:\Games\FridayNightFunkin\assets
  pause
  exit /b 1
)

set "PYTHON_EXE=python"
where python >nul 2>nul
if errorlevel 1 set "PYTHON_EXE=py -3"

if not exist ".venv\Scripts\python.exe" (
  echo [FoxFunkin] Creating Python venv...
  %PYTHON_EXE% -m venv .venv
  if errorlevel 1 goto :fail
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :fail
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail
python -m foxfunkin.tools.import_assets "%~1"
if errorlevel 1 goto :fail

echo.
echo Done. Now run:
echo   check_assets.bat
echo   run.bat
pause
exit /b 0

:fail
echo.
echo Import failed. Check that the path exists and contains FNF-compatible assets.
pause
exit /b 1
