# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
用于打包 CloudPortalService
"""

import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('service_config.json', '.')],
    hiddenimports=[
        'flask',
        'flask_cors',
        'werkzeug',
        'werkzeug.serving',
        'requests',
        'urllib3',
        'json',
        'logging',
        'threading',
        'socket',
        'hashlib',
        'base64',
        'uuid',
        'time',
        'datetime',
        'collections',
        'typing',
        'websocket',
        'websockets',
        'ddddocr',
        'captcha_ocr',
        'onnxruntime',
        'onnxruntime.capi',
        'onnxruntime.capi.onnxruntime_pybind11_state',
        'PIL',
        'PIL.Image',
        'PIL.ImageEnhance',
        'PIL._imaging',
        'numpy',
        'numpy.core',
        'numpy.core._methods',
        'protobuf',
        'google',
        'google.protobuf',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CloudPortalService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
