@echo off
REM ==============================================================================
REM UwawConnect v1.0 Automated Installer for Windows (CMD / PowerShell)
REM Wownet Network Infrastructure Operations
REM ==============================================================================

echo.
echo ==============================================================================
echo  UWAWCONNECT v1.0 -- Automated Windows Installer Script
echo ==============================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Python 3 is missing on this Windows system.
    echo [!] Attempting automatic Python installation via winget...
    winget install Python.Python.3 --silent --accept-package-agreements --accept-source-agreements >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Winget failed to install Python. Please download Python from https://www.python.org/
        pause
        exit /b 1
    )
)

echo [+] Python 3 environment detected.

echo [+] Verifying PySerial library...
pip install pyserial >nul 2>nul
echo [+] PySerial library verified.

set "WIN_APP_DIR=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps"
if not exist "%WIN_APP_DIR%" mkdir "%WIN_APP_DIR%"

set "SCRIPT_SRC=%~dp0uwawconnect.py"

echo @echo off > "%WIN_APP_DIR%\uwaw.cmd"
echo python "%SCRIPT_SRC%" %%* >> "%WIN_APP_DIR%\uwaw.cmd"

echo.
echo ==============================================================================
echo  [SUCCESS] UwawConnect v1.0 Installed Successfully on Windows!
echo  Open Command Prompt or PowerShell, then type:
echo  uwaw
echo ==============================================================================
echo.
pause
