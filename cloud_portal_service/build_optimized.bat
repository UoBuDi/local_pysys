@echo off
chcp 65001 >nul 2>&1
cls

echo ============================================
echo   CloudPortalService 优化打包脚本
echo ============================================
echo.

echo [1/5] 检查依赖...
python -m pip install --upgrade pip --quiet 2>nul
python -m pip install pyside6 flask flask-cors requests websocket-client pyinstaller --quiet 2>nul

echo [2/5] 更新版本信息...
python update_version.py 2>nul

echo [3/5] 清理旧的构建文件...
if exist dist rmdir /s /q dist 2>nul
if exist build rmdir /s /q build 2>nul

echo [4/5] 开始打包 (优化模式)...
echo    - 隐藏控制台窗口
echo    - 启用UPX压缩
echo    - 排除不需要的模块
echo.

pyinstaller --clean --noconfirm build_optimized.spec

if %ERRORLEVEL% neq 0 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo [5/5] 复制配置文件...
copy /y service_config.json dist\service_config.json >nul 2>nul

echo.
echo ============================================
echo   打包完成！
echo ============================================
echo.
echo 输出文件: dist\CloudPortalService.exe
echo 配置文件: dist\service_config.json
echo.

for %%A in (dist\CloudPortalService.exe) do echo 文件大小: %%~zA 字节 (约 %%~zAKB)

echo.
pause
