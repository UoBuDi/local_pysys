@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo    Cloud Portal Service Starter
echo ========================================
echo.

cd /d "%~dp0"

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install Flask==3.0.0 Flask-CORS==4.0.0 requests==2.31.0 PySide6==6.6.1 werkzeug==3.0.1 -q

echo.
echo Starting service...
python main.py

pause
