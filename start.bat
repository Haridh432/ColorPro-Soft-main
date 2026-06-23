@echo off
title ColorPro — Starting Servers
color 0B

echo.
echo ================================================
echo   ColorPro — Development Server
echo ================================================
echo.

:: ── Start Backend ──
echo [Backend] Starting Django on http://localhost:8000 ...
cd /d "%~dp0backend"

echo   Running migrations...
call venv\Scripts\python.exe manage.py migrate --noinput 2>nul

start "ColorPro Backend" venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

:: ── Start Frontend ──
echo [Frontend] Starting Next.js on http://localhost:3000 ...
cd /d "%~dp0frontend"
start "ColorPro Frontend" cmd /c "npm run dev"

:: ── Done ──
echo.
echo ================================================
echo   Both servers are running!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   Admin:    http://localhost:8000/admin/
echo ================================================
echo.
echo Close this window or press any key to stop.
pause >nul
taskkill /FI "WINDOWTITLE eq ColorPro Backend" /F 2>nul
taskkill /FI "WINDOWTITLE eq ColorPro Frontend" /F 2>nul
echo Servers stopped.
