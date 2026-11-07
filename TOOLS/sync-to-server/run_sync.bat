@echo off
setlocal
chcp 65001 >nul
"D:\Anaconda\python.exe" -X utf8 -B "%~dp0sync.py" snapshot --document-index "%~dp0..\..\追溯文档\source\README.md"
set "sync_exit=%errorlevel%"
echo.
pause
exit /b %sync_exit%
