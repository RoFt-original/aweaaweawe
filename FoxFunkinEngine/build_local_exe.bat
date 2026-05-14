@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo  FoxFunkinEngine local Windows EXE build
echo ============================================================
echo.

set "WITH_LOCAL_DATA=0"
if /I "%~1"=="--with-local-data" set "WITH_LOCAL_DATA=1"

set "PYTHON_LAUNCHER=python"
where python >nul 2>nul
if errorlevel 1 set "PYTHON_LAUNCHER=py -3"

echo [1/6] Checking Python...
%PYTHON_LAUNCHER% --version
if errorlevel 1 (
  echo.
  echo [ERROR] Python 3.11+ was not found.
  echo Install Python 3.11+ and enable Add Python to PATH.
  pause
  exit /b 1
)

echo.
echo [2/6] Creating/updating virtual environment...
if not exist ".venv\Scripts\python.exe" (
  %PYTHON_LAUNCHER% -m venv .venv
  if errorlevel 1 goto :fail
)
call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :fail

echo.
echo [3/6] Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 goto :fail
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail
python -m pip install pyinstaller
if errorlevel 1 goto :fail

echo.
echo [4/6] Checking Python files...
python -m compileall -q foxfunkin run_engine.py run_tools.py
if errorlevel 1 goto :fail

echo.
echo [5/6] Building EXE files...
pyinstaller --noconfirm --clean --onefile --windowed --name FoxFunkinEngine run_engine.py
if errorlevel 1 goto :fail
pyinstaller --noconfirm --clean --onefile --windowed --name FoxFunkinTools run_tools.py
if errorlevel 1 goto :fail

echo.
echo [6/6] Preparing dist folder...
if not exist "dist\data" mkdir "dist\data"
if not exist "dist\mods" mkdir "dist\mods"
if not exist "dist\docs" mkdir "dist\docs"
if exist "README_RU.md" copy /Y "README_RU.md" "dist\README_RU.txt" >nul
if exist "docs" xcopy /E /I /Y "docs" "dist\docs" >nul
if exist "mods\example_10min_mod" xcopy /E /I /Y "mods\example_10min_mod" "dist\mods\example_10min_mod" >nul
if exist "data\README_PUT_ASSETS_HERE.txt" copy /Y "data\README_PUT_ASSETS_HERE.txt" "dist\data\README_PUT_ASSETS_HERE.txt" >nul

if "%WITH_LOCAL_DATA%"=="1" (
  echo [FoxFunkin] Copying local data into private build...
  if exist "data" xcopy /E /I /Y "data" "dist\data" >nul
) else (
  echo [FoxFunkin] Public release mode: local data assets were not copied.
  echo [FoxFunkin] To include your own local data folder, run:
  echo   build_local_exe.bat --with-local-data
)

echo.
echo ============================================================
echo  DONE
echo ============================================================
echo Built files:
echo   %CD%\dist\FoxFunkinEngine.exe
echo   %CD%\dist\FoxFunkinTools.exe
echo.
pause
exit /b 0

:fail
echo.
echo ============================================================
echo  BUILD FAILED
echo ============================================================
echo Check the error above. Common fixes:
echo - Install Python 3.11+
echo - Run this file from the FoxFunkinEngine folder
echo - Delete .venv and try again if dependencies broke
echo.
pause
exit /b 1
