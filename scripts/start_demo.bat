@echo off
setlocal
cd /d "%~dp0"
title Persian Site Assistant Demo

:menu
cls
echo ==========================================
echo        Persian Site Assistant Demo
echo ==========================================
echo.
echo   1. Native Windows mode  (no Docker)
echo   2. Docker mode
echo   Q. Exit
echo.
choice /c 12Q /n /m "Choose how to run the demo: "

if errorlevel 3 goto :eof
if errorlevel 2 goto docker
if errorlevel 1 goto native

:native
if not exist "%~dp0native\PersianSiteAssistant.exe" (
    echo.
    echo Native application files are missing.
    echo Re-copy the complete demo folder.
    pause
    goto menu
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0START-NATIVE.ps1"
if errorlevel 1 (
    echo.
    echo The native launcher reported an error.
    pause
)
goto menu

:docker
if not exist "%~dp0docker\images.tar" (
    echo.
    echo Docker mode is not included in this package.
    echo Select Native Windows mode to start the demo without Docker.
    pause
    goto menu
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0docker\START-HERE.ps1"
if errorlevel 1 (
    echo.
    echo The Docker launcher reported an error.
    pause
)
goto menu
