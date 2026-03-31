@echo off
chcp 65001 >nul
echo ========================================
echo 数据管理系统 - 开发运行
echo ========================================
echo.

cd /d "%~dp0"

echo 启动GUI应用程序...
python main.py

if errorlevel 1 (
    echo.
    echo 程序异常退出
    pause
)
