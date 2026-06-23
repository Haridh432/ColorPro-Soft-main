@echo off
title ColorPro — Setup Environment
color 0B

echo.
echo ================================================
echo   ColorPro — Environment Setup
echo ================================================
echo.

:: ── Setup Backend ──
echo [Backend] Setting up Python virtual environment...
cd /d "%~dp0backend"

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

echo.
echo [Backend] Installing requirements...
call venv\Scripts\activate.bat
pip install -r requirements.txt
call deactivate

echo.
if not exist ".env" (
    echo [Backend] Creating .env from .env.example...
    copy .env.example .env
)

echo.
echo [Backend] Running migrations...
call venv\Scripts\python.exe manage.py migrate

:: ── Setup Frontend ──
echo.
echo [Frontend] Installing Node.js packages...
cd /d "%~dp0frontend"
call npm install

:: ── Done ──
echo.
echo ================================================
echo   Setup Complete!
echo   You can now run 'start.bat' to start the servers.
echo ================================================
echo.
pause
