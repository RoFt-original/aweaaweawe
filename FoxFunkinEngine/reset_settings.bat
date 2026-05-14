@echo off
cd /d "%~dp0"
if exist settings.json del settings.json
echo settings.json removed. Engine will recreate it on next run.
pause
