@echo off
chcp 65001 >nul 2>&1
cls

echo ============================================
echo   CloudPortalService Nuitka 打包脚本
echo ============================================
echo.

echo [1/4] 检查并安装依赖...
python -m pip install --upgrade pip --quiet 2>nul
python -m pip install nuitka zstandard ordered-set --quiet 2>nul

echo [2/4] 清理旧的构建文件...
if exist dist rmdir /s /q dist 2>nul
if exist build rmdir /s /q build 2>nul
if exist main.build rmdir /s /q main.build 2>nul
if exist main.dist rmdir /s /q main.dist 2>nul
if exist main.onefile-build rmdir /s /q main.onefile-build 2>nul

echo [3/4] 开始 Nuitka 编译...
echo    - 隐藏控制台窗口
echo    - 单文件打包
echo    - 内置压缩 (约 25%% 压缩率)
echo.

python -m nuitka ^
    --onefile ^
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
echo [4/4] 验证输出文件...
if exist dist\CloudPortalService.exe (
    for %%A in (dist\CloudPortalService.exe) do (
        set SIZE=%%~zA
        set /a SIZE_MB=%%~zA/1048576
        echo 文件大小: %%~zA 字节 (约 !SIZE_MB! MB)
    )
) else (
    echo [警告] 未找到输出文件！
)

echo.
echo ============================================
echo   打包完成！
echo ============================================
echo.
echo 输出文件: dist\CloudPortalService.exe
echo 配置文件: service_config.json (已内嵌)
echo.
echo 注意: 运行时需要 service_config.json 在同一目录
echo.
pause
