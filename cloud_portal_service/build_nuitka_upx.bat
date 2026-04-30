@echo off
chcp 65001 >nul 2>&1
cls
setlocal enabledelayedexpansion

echo ============================================
echo   CloudPortalService Nuitka + UPX 打包脚本
echo ============================================
echo.

set UPX_PATH=d:\local_pysys\cloud_portal_service\upx-4.2.4-win64\upx.exe
set DIST_DIR=dist\main.dist

echo [1/5] 检查依赖...
python -m pip install --upgrade pip --quiet 2>nul
python -m pip install nuitka zstandard ordered-set --quiet 2>nul

if not exist "%UPX_PATH%" (
    echo [错误] UPX 未找到: %UPX_PATH%
    echo 请确保 upx-4.2.4-win64 目录存在
    pause
    exit /b 1
)
echo UPX 已就绪: %UPX_PATH%

echo [2/5] 清理旧的构建文件...
if exist dist rmdir /s /q dist 2>nul
if exist build rmdir /s /q build 2>nul
if exist main.build rmdir /s /q main.build 2>nul
if exist main.dist rmdir /s /q main.dist 2>nul
if exist main.onefile-build rmdir /s /q main.onefile-build 2>nul

echo [3/5] 开始 Nuitka 编译 (standalone 模式)...
echo    - 隐藏控制台窗口
echo    - 独立目录模式
echo    - 包含所有必要模块
echo.

python -m nuitka ^
    --standalone ^
    --windows-console-mode=disable ^
    --enable-plugin=pyside6 ^
    --output-dir=dist ^
    --output-filename=CloudPortalService.exe ^
    --include-module=flask ^
    --include-module=flask_cors ^
    --include-module=werkzeug ^
    --include-module=werkzeug.serving ^
    --include-module=requests ^
    --include-module=urllib3 ^
    --include-module=websocket ^
    --include-module=websockets ^
    --include-module=json ^
    --include-module=logging ^
    --include-module=threading ^
    --include-module=socket ^
    --include-module=hashlib ^
    --include-module=base64 ^
    --include-module=uuid ^
    --include-module=time ^
    --include-module=datetime ^
    --include-module=collections ^
    --include-module=typing ^
    --include-module=dataclasses ^
    --include-module=atexit ^
    --include-module=signal ^
    --include-module=random ^
    --include-module=re ^
    --include-module=inspect ^
    --include-module=dis ^
    --include-module=argparse ^
    --include-module=shutil ^
    --include-module=zipfile ^
    --include-module=zlib ^
    --include-module=gzip ^
    --include-module=bz2 ^
    --include-module=lzma ^
    --include-module=tarfile ^
    --include-module=pickle ^
    --include-module=codecs ^
    --include-module=io ^
    --include-module=os ^
    --include-module=sys ^
    --include-module=pathlib ^
    --include-module=tempfile ^
    --include-module=functools ^
    --include-module=itertools ^
    --include-module=operator ^
    --include-module=copy ^
    --include-module=pprint ^
    --include-module=enum ^
    --include-module=contextlib ^
    --include-module=warnings ^
    --include-module=traceback ^
    --include-module=weakref ^
    --include-module=types ^
    --include-module=abc ^
    --include-module=numbers ^
    --include-module=decimal ^
    --include-module=fractions ^
    --include-module=statistics ^
    --include-module=math ^
    --include-module=cmath ^
    --include-module=string ^
    --include-module=textwrap ^
    --include-module=unicodedata ^
    --include-module=struct ^
    --include-module=encodings ^
    --include-data-file=service_config.json=service_config.json ^
    --assume-yes-for-downloads ^
    --show-progress ^
    --lto=yes ^
    main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [错误] Nuitka 编译失败！
    pause
    exit /b 1
)

echo.
echo [4/5] 使用 UPX 压缩文件...

echo 压缩主程序...
"%UPX_PATH%" --best --lzma "%DIST_DIR%\CloudPortalService.exe"

echo 压缩 PySide6 模块...
"%UPX_PATH%" --best --lzma "%DIST_DIR%\PySide6\QtCore.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\PySide6\QtGui.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\PySide6\QtWidgets.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\PySide6\QtNetwork.pyd" 2>nul

echo 压缩 shiboken6 模块...
"%UPX_PATH%" --best --lzma "%DIST_DIR%\shiboken6\Shiboken.pyd" 2>nul

echo 压缩 Python 标准库...
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_asyncio.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_bz2.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_cffi_backend.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_ctypes.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_decimal.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_hashlib.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_lzma.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_multiprocessing.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_overlapped.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_queue.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_socket.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_ssl.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\_wmi.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\pyexpat.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\select.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\unicodedata.pyd" 2>nul

echo 压缩第三方模块...
"%UPX_PATH%" --best --lzma "%DIST_DIR%\bcrypt\_bcrypt.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\cryptography\hazmat\bindings\_rust.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\markupsafe\_speedups.pyd" 2>nul

echo 压缩 PIL 模块...
"%UPX_PATH%" --best --lzma "%DIST_DIR%\PIL\_imaging.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\PIL\_imagingcms.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\PIL\_imagingmath.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\PIL\_imagingtk.pyd" 2>nul
"%UPX_PATH%" --best --lzma "%DIST_DIR%\PIL\_webp.pyd" 2>nul

echo.
echo [5/5] 验证输出...
if exist "%DIST_DIR%\CloudPortalService.exe" (
    for %%A in ("%DIST_DIR%\CloudPortalService.exe") do (
        set SIZE=%%~zA
        set /a SIZE_MB=%%~zA/1048576
        echo 主程序大小: %%~zA 字节 (约 !SIZE_MB! MB)
    )
) else (
    echo [警告] 未找到输出文件！
)

echo.
echo ============================================
echo   打包完成！
echo ============================================
echo.
echo 输出目录: %DIST_DIR%
echo 主程序: CloudPortalService.exe
echo 配置文件: service_config.json (已内嵌)
echo.
echo 注意: 运行时需要整个 main.dist 目录
echo.
pause
