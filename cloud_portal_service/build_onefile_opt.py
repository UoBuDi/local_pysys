"""
Nuitka Onefile 编译脚本

核心策略:
  1. onefile 编译（单文件模式）
  2. 所有模块和依赖打包进单个 exe
  3. 运行时自解压到临时目录，无需外部依赖

注意:
  - onefile 模式启动时会将文件解压到临时目录，首次启动稍慢
  - 生成的单文件 exe 包含所有依赖，可直接分发
"""

import os
import sys
import subprocess


os.environ["NUITKA_CACHE_DIR"] = r"D:\local_pysys\cloud_portal_service\.nuitka_cache"

PROJECT_DIR = r"D:\local_pysys\cloud_portal_service"
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
OUTPUT_FILENAME = "CloudPortalService.exe"

SITE_PACKAGES = r"D:\local_pysys\.venv\Lib\site-packages"


def get_common_nuitka_args():
    """Nuitka 编译参数（与 standalone 共用）"""
    ddddocr_dir = os.path.join(SITE_PACKAGES, "ddddocr")

    args = [
        "--windows-console-mode=disable",
        "--enable-plugin=pyside6",
        "--output-dir=dist",
        "--output-filename=CloudPortalService.exe",

        # === 核心业务模块 ===
        "--include-module=flask",
        "--include-module=flask_cors",
        "--include-module=werkzeug",
        "--include-module=werkzeug.serving",
        "--include-module=requests",
        "--include-module=urllib3",
        "--include-module=websocket",
        "--include-module=ddddocr",
        "--include-package-data=ddddocr",
        "--include-module=captcha_ocr",
        "--include-module=onnxruntime",
        "--include-module=PIL",
        "--include-module=PIL.Image",
        "--include-module=PIL.ImageEnhance",
        "--include-module=numpy",

        # === ONNX 模型文件（显式包含，防 --include-package-data 遗漏）===
        f"--include-data-files={ddddocr_dir}/common_old.onnx=ddddocr/common_old.onnx",
        f"--include-data-files={ddddocr_dir}/common.onnx=ddddocr/common.onnx",
        f"--include-data-files={ddddocr_dir}/common_det.onnx=ddddocr/common_det.onnx",
        f"--include-data-files={ddddocr_dir}/charsets.py=ddddocr/charsets.py",

        # === Flask/Werkzeug 传递依赖（防御性包含）===
        "--include-module=jinja2",
        "--include-module=markupsafe",

        # === 排除不需要的模块（减小体积）===
        "--nofollow-import-to=cv2",
        "--nofollow-import-to=opencv-python",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=PySide6.QtWebEngine",
        "--nofollow-import-to=PySide6.QtWebEngineCore",
        "--nofollow-import-to=PySide6.QtWebEngineWidgets",
        "--nofollow-import-to=PySide6.QtQuick",
        "--nofollow-import-to=PySide6.QtQuickWidgets",
        "--nofollow-import-to=PySide6.QtQml",
        "--nofollow-import-to=PySide6.QtDesigner",
        "--nofollow-import-to=PySide6.QtPdf",
        "--nofollow-import-to=PySide6.QtPdfWidgets",
        "--nofollow-import-to=PySide6.Qt3D",
        "--nofollow-import-to=PySide6.Qt3DCore",
        "--nofollow-import-to=PySide6.Qt3DRender",
        "--nofollow-import-to=PySide6.Qt3DInput",
        "--nofollow-import-to=PySide6.Qt3DLogic",
        "--nofollow-import-to=PySide6.Qt3DExtras",
        "--nofollow-import-to=PySide6.QtOpenGL",
        "--nofollow-import-to=PySide6.QtOpenGLWidgets",
        "--nofollow-import-to=PySide6.QtShaderTools",
        "--nofollow-import-to=PySide6.QtMultimedia",
        "--nofollow-import-to=PySide6.QtMultimediaWidgets",
        "--nofollow-import-to=PySide6.QtNetwork",
        "--nofollow-import-to=PySide6.QtSensors",
        "--nofollow-import-to=PySide6.QtBluetooth",
        "--nofollow-import-to=PySide6.QtPositioning",
        "--nofollow-import-to=PySide6.QtLocation",
        "--nofollow-import-to=PySide6.QtXml",
        "--nofollow-import-to=PySide6.QtSvg",
        "--nofollow-import-to=PySide6.QtSvgWidgets",
        "--nofollow-import-to=PySide6.QtSql",
        "--nofollow-import-to=PySide6.QtTest",
        "--nofollow-import-to=PySide6.QtHelp",
        "--nofollow-import-to=PySide6.QtPrintSupport",
        "--nofollow-import-to=PySide6.QtTextToSpeech",
        "--nofollow-import-to=PySide6.QtSerialPort",
        "--nofollow-import-to=PySide6.QtWebChannel",
        "--nofollow-import-to=PySide6.QtWebSockets",
        "--nofollow-import-to=PySide6.QtNfc",
        "--nofollow-import-to=PySide6.QtCharts",
        "--nofollow-import-to=PySide6.QtDataVisualization",
        "--nofollow-import-to=unittest",
        "--nofollow-import-to=pytest",
        "--nofollow-import-to=setuptools",
        "--nofollow-import-to=pip",
        "--nofollow-import-to=wheel",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=turtledemo",
        "--nofollow-import-to=idlelib",
        "--nofollow-import-to=distutils",
        "--nofollow-import-to=lib2to3",
        "--nofollow-import-to=ensurepip",
        "--nofollow-import-to=venv",
        "--nofollow-import-to=pydoc",
        "--nofollow-import-to=pydoc_data",
        "--nofollow-import-to=doctest",
        "--nofollow-import-to=py_compile",
        "--nofollow-import-to=compileall",
        "--nofollow-import-to=xmlrpc",
        "--nofollow-import-to=test",
        "--nofollow-import-to=tests",

        # === 数据文件与编译选项 ===
        "--include-data-file=service_config.json=service_config.json",
        "--assume-yes-for-downloads",
        "--show-progress",
        "--lto=yes",
    ]

    return args


def compile_onefile():
    """执行 Nuitka onefile 编译"""
    print("\n[1/1] Nuitka onefile 编译...")

    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        # onefile 模式下指定临时解压目录，避免每次解压到不同位置
        "--onefile-tempdir-spec={CACHE_DIR}/CloudPortalService/runtime",
    ] + get_common_nuitka_args() + ["main.py"]

    print(f"  命令: {' '.join(cmd[:6])}... (共 {len(cmd)} 个参数)")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    if result.returncode != 0:
        print(f"  错误: onefile 编译失败 (exit code {result.returncode})")
        sys.exit(result.returncode)

    exe_path = os.path.join(DIST_DIR, OUTPUT_FILENAME)
    if not os.path.isfile(exe_path):
        print("  错误: exe 文件未生成")
        sys.exit(1)

    exe_size = os.path.getsize(exe_path) / (1024 * 1024)

    print(f"\n  ✅ onefile 编译完成!")
    print(f"     输出文件: {exe_path}")
    print(f"     文件大小: {exe_size:.2f} MB")
    print(f"\n  部署方式: 将 CloudPortalService.exe 复制到目标机器即可运行")

    return exe_path


def main():
    print("=" * 60)
    print("Nuitka Onefile 编译")
    print("  模式: onefile（单文件）")
    print("  特点: 所有依赖打包进单个 exe，直接分发")
    print("")
    print("  包含依赖:")
    print("    - PySide6 GUI + Flask API")
    print("    - ddddocr>=1.6.1 完整版 (含 ONNX 模型 ~84MB)")
    print("    - onnxruntime (含原生 DLL)")
    print("    - PIL / numpy / requests / websocket")
    print("=" * 60)

    compile_onefile()


if __name__ == "__main__":
    main()
