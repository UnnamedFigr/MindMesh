@echo off
title MindMesh Launcher
echo ========================================
echo        MindMesh - Starting...
echo ========================================
echo.

:: Clean up stale lock files
del /f /q "%~dp0frontend\.next\dev\lock" 2>nul

:: Start backend in a new window
echo [1/2] Starting backend (port 8000)...
start "MindMesh Backend" /D "%~dp0backend" cmd /k "venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

:: Give backend a moment to boot
timeout /t 3 /nobreak >nul

:: Start frontend in a new window
echo [2/2] Starting frontend (port 3000)...
start "MindMesh Frontend" /D "%~dp0frontend" cmd /k "pnpm dev"

echo.
echo ========================================
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:3000
echo  Dev Mode: http://localhost:3000/dev
echo ========================================
echo.
echo Close this window anytime. The servers
echo will keep running in their own windows.
echo.
pause
