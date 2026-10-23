@echo off
setlocal
set "CURRENT_DIR=%~dp0"
set "PROJECT_DIR=%CURRENT_DIR%MoneyPrinterTurbo"
echo ***** Current directory: %CURRENT_DIR% *****

if not exist "%PROJECT_DIR%\webui\Main.py" (
    echo ***** MoneyPrinterTurbo source directory was not found: %PROJECT_DIR% *****
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo ***** Unable to enter MoneyPrinterTurbo source directory: %PROJECT_DIR% *****
    pause
    exit /b 1
)

if defined PYTHONPATH (
    set "PYTHONPATH=%PROJECT_DIR%;%PYTHONPATH%"
) else (
    set "PYTHONPATH=%PROJECT_DIR%"
)

set "FFMPEG_BINARY=%CURRENT_DIR%lib\ffmpeg\ffmpeg-7.0-essentials_build\ffmpeg.exe"
echo ***** FFmpeg file: %FFMPEG_BINARY% *****

set "USER_HOME=%USERPROFILE%"
set "STREAMLIT_DIR=%USER_HOME%\.streamlit"
set "CREDENTIAL_FILE=%STREAMLIT_DIR%\credentials.toml"
if not exist "%STREAMLIT_DIR%" (
    mkdir "%STREAMLIT_DIR%"
    (
        echo [general]
        echo email=""
    ) > "%CREDENTIAL_FILE%"
)


if not defined MPT_WEBUI_HOST set "MPT_WEBUI_HOST=127.0.0.1"
if not defined MPT_WEBUI_PORT set "MPT_WEBUI_PORT=8501"

set "SELECTED_WEBUI_PORT="
for /f %%P in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$hostAddress=$null; foreach ($address in [Net.Dns]::GetHostAddresses($env:MPT_WEBUI_HOST)) { if ($address.AddressFamily -eq [Net.Sockets.AddressFamily]::InterNetwork) { $hostAddress=$address; break } }; if ($null -eq $hostAddress) { exit 1 }; $preferred=[int]$env:MPT_WEBUI_PORT; $candidates=New-Object System.Collections.Generic.List[int]; $candidates.Add($preferred); foreach ($candidate in 8502..8599) { if ($candidate -ne $preferred) { $candidates.Add($candidate) } }; foreach ($port in $candidates) { $socket=[Net.Sockets.Socket]::new([Net.Sockets.AddressFamily]::InterNetwork,[Net.Sockets.SocketType]::Stream,[Net.Sockets.ProtocolType]::Tcp); try { $socket.Bind([Net.IPEndPoint]::new($hostAddress,$port)); $socket.Close(); Write-Output $port; exit 0 } catch { try { $socket.Close() } catch {} } }; exit 1"') do set "SELECTED_WEBUI_PORT=%%P"

if not defined SELECTED_WEBUI_PORT (
    echo ***** No available WebUI port found in 8501-8599 for %MPT_WEBUI_HOST%. *****
    echo ***** If Windows reports WinError 10013, check reserved ports: netsh interface ipv4 show excludedportrange protocol=tcp *****
    pause
    exit /b 1
)

if not "%SELECTED_WEBUI_PORT%"=="%MPT_WEBUI_PORT%" (
    echo ***** Port %MPT_WEBUI_PORT% is unavailable, using %SELECTED_WEBUI_PORT% instead. *****
)
set "MPT_WEBUI_PORT=%SELECTED_WEBUI_PORT%"

echo ***** WebUI address: http://%MPT_WEBUI_HOST%:%MPT_WEBUI_PORT% *****
"%CURRENT_DIR%lib\python\python.exe" -m streamlit run "%PROJECT_DIR%\webui\Main.py" --server.address=%MPT_WEBUI_HOST% --server.port=%MPT_WEBUI_PORT% --browser.serverAddress=%MPT_WEBUI_HOST% --browser.gatherUsageStats=False --server.enableCORS=True
