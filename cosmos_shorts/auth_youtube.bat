@echo off
setlocal
set "COSMOS_DIR=%~dp0"
set "CURRENT_DIR=%COSMOS_DIR%..\"
cd /d "%COSMOS_DIR%"

"%CURRENT_DIR%lib\python\python.exe" auth_youtube.py
pause
