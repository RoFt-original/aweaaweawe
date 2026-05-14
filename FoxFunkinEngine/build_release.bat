@echo off
setlocal
cd /d "%~dp0"
set "WITH_LOCAL_DATA=0"
if /I "%~1"=="--with-local-data" set "WITH_LOCAL_DATA=1"
set "PYTHON_EXE=python"
where python >nul 2>nul || set "PYTHON_EXE=py -3"
if not exist ".venv\Scripts\python.exe" (
  echo [FoxFunkin] Creating Python venv...
  %PYTHON_EXE% -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [FoxFunkin] Building engine and tools...
pyinstaller --noconfirm --clean --onefile --windowed --name FoxFunkinEngine run_engine.py
pyinstaller --noconfirm --clean --onefile --windowed --name FoxFunkinTools run_tools.py

echo [FoxFunkin] Preparing release folders...
if not exist "dist\data" mkdir "dist\data"
if not exist "dist\mods" mkdir "dist\mods"
if not exist "dist\docs" mkdir "dist\docs"
copy /Y "README_RU.md" "dist\README_RU.txt" >nul
xcopy /E /I /Y "docs" "dist\docs" >nul
xcopy /E /I /Y "mods\example_10min_mod" "dist\mods\example_10min_mod" >nul
copy /Y "data\README_PUT_ASSETS_HERE.txt" "dist\data\README_PUT_ASSETS_HERE.txt" >nul
if "%WITH_LOCAL_DATA%"=="1" (
  echo [FoxFunkin] Copying local data for private build...
  xcopy /E /I /Y "data" "dist\data" >nul
) else (
  echo [FoxFunkin] Public release mode: original/local data assets were not copied.
)

echo.
echo Built:
echo   dist\FoxFunkinEngine.exe
echo   dist\FoxFunkinTools.exe
echo.
pause
