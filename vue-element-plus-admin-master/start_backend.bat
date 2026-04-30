@echo off
chcp 65001 >nul 2>&1
title GUI Service Backend Server - Port 8000
color 0A

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║           GUI Service Backend Server                      ║
echo ║           Starting Up...                                   ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0backend"

if not exist main.py (
    echo [ERROR] Cannot find main.py in backend directory!
    echo Please ensure this script is in the project root directory.
    pause
    exit /b 1
)

echo [INFO] Working Directory: %cd%
echo [INFO] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo [INFO] Checking uvicorn package...
python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] uvicorn not found, installing...
    pip install uvicorn[standard]
)

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║           Starting Uvicorn Server...                       ║
echo ║           Host: http://0.0.0.0:8000                       ║
echo ║           Mode:  Reload (Auto-restart on code changes)    ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║           Press CTRL+C to stop the server                  ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo [INFO] Server stopped.
pause
