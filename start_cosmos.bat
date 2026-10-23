@echo off
chcp 65001 >nul
title COSMOS GROWTH OS — YouTube Command Center

echo =====================================================================
echo           🪐 COSMOS GROWTH OS — YouTube Command Center
echo                 Target Channel: COSMOS VIRAL
echo =====================================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "PYTHON_EXE=%SCRIPT_DIR%lib\python\python.exe"
set "FFMPEG_DIR=%SCRIPT_DIR%lib\ffmpeg\ffmpeg-7.0-essentials_build"
set "FFMPEG_BINARY=%FFMPEG_DIR%\ffmpeg.exe"
set "PYTHONPATH=%SCRIPT_DIR%cosmos_growth_os;%SCRIPT_DIR%cosmos_shorts;%SCRIPT_DIR%MoneyPrinterTurbo"
set "PATH=%FFMPEG_DIR%;%PATH%"

:: 1. Verify Python
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Portable Python not found at %PYTHON_EXE%
    pause
    exit /b 1
)

:: 2. Check Ollama Status
echo [1/3] Checking Ollama Local AI Service...
curl -s -m 2 http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [NOTICE] Ollama does not appear to be running on http://localhost:11434.
    echo          Please start Ollama in another window if you plan to generate AI scripts.
    echo          (The dashboard will still open and display all YouTube analytics and past videos.)
) else (
    echo [OK] Ollama is active with Qwen models!
)
echo.

:: 3. Launch Default Browser
echo [2/3] Launching Web Interface...
start http://127.0.0.1:8500
echo.

:: 4. Start FastAPI Server
echo [3/3] Starting COSMOS Growth OS Server at http://127.0.0.1:8500...
echo.
echo =====================================================================
echo   Application Running!
echo   Open in browser: http://127.0.0.1:8500
echo   Press Ctrl+C to stop the server anytime.
echo =====================================================================
echo.

"%PYTHON_EXE%" -m uvicorn backend.app:app --app-dir "%SCRIPT_DIR%cosmos_growth_os" --host 127.0.0.1 --port 8500

pause
