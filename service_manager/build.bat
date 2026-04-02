@echo off
chcp 65001 >nul
echo ========================================
echo 服务管理工具打包脚本
echo ========================================

echo.
echo [1/3] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo.
echo [2/3] 安装依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [3/3] 开始打包...
pyinstaller --onefile --windowed --name "ServiceManager" --icon=icon.ico --add-data "icon.ico;." main.py

echo.
echo ========================================
echo 打包完成！
echo 可执行文件位于: dist\ServiceManager.exe
echo ========================================
pause
