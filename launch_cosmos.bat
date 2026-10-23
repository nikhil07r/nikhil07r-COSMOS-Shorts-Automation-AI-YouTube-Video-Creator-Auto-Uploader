@echo off
setlocal
set "CURRENT_DIR=%~dp0"
set "COSMOS_DIR=%CURRENT_DIR%cosmos_shorts"
set "PROJECT_DIR=%CURRENT_DIR%MoneyPrinterTurbo"
echo ===================================================
echo   COSMOS YouTube Shorts Studio - Launcher
echo ===================================================

if not exist "%COSMOS_DIR%\cosmos_dashboard.py" (
    echo [ERROR] cosmos_dashboard.py not found in %COSMOS_DIR%!
    pause
    exit /b 1
)

cd /d "%COSMOS_DIR%"

if defined PYTHONPATH (
    set "PYTHONPATH=%COSMOS_DIR%;%PROJECT_DIR%;%PYTHONPATH%"
) else (
    set "PYTHONPATH=%COSMOS_DIR%;%PROJECT_DIR%"
)

set "FFMPEG_BINARY=%CURRENT_DIR%lib\ffmpeg\ffmpeg-7.0-essentials_build\ffmpeg.exe"
set "PATH=%CURRENT_DIR%lib\ffmpeg\ffmpeg-7.0-essentials_build;%PATH%"

set "COSMOS_PORT=8502"
echo Starting COSMOS Studio at http://127.0.0.1:%COSMOS_PORT% ...
echo (Opening in your browser... Press Ctrl+C to stop)
echo.

start "" http://127.0.0.1:%COSMOS_PORT%

"%CURRENT_DIR%lib\python\python.exe" -m streamlit run "%COSMOS_DIR%\cosmos_dashboard.py" --server.address=127.0.0.1 --server.port=%COSMOS_PORT% --browser.serverAddress=127.0.0.1 --browser.gatherUsageStats=False --server.enableCORS=True

pause
