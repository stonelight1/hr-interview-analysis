@echo off
setlocal

where pwsh.exe >nul 2>nul
if %ERRORLEVEL% equ 0 (
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" -FrontendOnly %*
) else (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" -FrontendOnly %*
)
exit /b %ERRORLEVEL%
