@echo off
setlocal
chcp 65001 >nul
rem 1 = keep only the current AI report; 0 = archive previous reports.
set "CLEAN_OLD_REPORTS=1"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_to_gdrive.ps1" -CleanOldReports %CLEAN_OLD_REPORTS%
set "sync_exit=%errorlevel%"
echo.
pause
exit /b %sync_exit%
