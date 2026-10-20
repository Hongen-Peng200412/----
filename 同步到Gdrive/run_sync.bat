@echo off
setlocal
chcp 65001 >nul
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_to_gdrive.ps1"
set "sync_exit=%errorlevel%"
echo.
pause
exit /b %sync_exit%
