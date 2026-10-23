@echo off
setlocal
set "CURRENT_DIR=%~dp0"
set "COSMOS_DIR=%CURRENT_DIR%cosmos_shorts"
cd /d "%COSMOS_DIR%"

"%CURRENT_DIR%lib\python\python.exe" auth_youtube.py
pause
