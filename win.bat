@echo off
chcp 65001 >nul 2>&1
title Mega Automation Hub (3-in-1)
set "DIR=%~dp0"
set "VENV=%DIR%venv"

echo ================================================================
echo   👑 MEGA AUTOMATION HUB — 3-IN-1 (WINDOWS)
echo ================================================================

if not exist "%VENV%\Scripts\python.exe" (
    echo [1/2] Virtual muhit yaratilmoqda...
    python -m venv "%VENV%"
    echo [2/2] Kerakli kutubxonalar o'rnatilmoqda...
    "%VENV%\Scripts\pip.exe" install -q fastapi uvicorn httpx
)

if exist "%VENV%\Scripts\python.exe" (
    "%VENV%\Scripts\python.exe" "%DIR%run.py" %*
) else (
    python "%DIR%run.py" %*
)

if %errorlevel% neq 0 (
    echo.
    echo Xatolik yuz berdi.
    pause
)
