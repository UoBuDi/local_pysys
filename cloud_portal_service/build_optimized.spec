# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata

block_cipher = None

hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'shiboken6',
    'flask',
    'flask_cors',
    'requests',
    'werkzeug',
    'werkzeug.serving',
    'werkzeug.serving.wsgi',
    'urllib3',
    'urllib3.util',
    'urllib3.util.connection',
    'charset_normalizer',
    'charset_normalizer.md__mypyc',
    'charset_normalizer.cd__mypyc',
    'websockets',
    'websocket',
    'websocket._abnf',
    'websocket._app',
    'websocket._core',
    'websocket._exceptions',
    'websocket._handshake',
    'websocket._http',
    'websocket._logging',
    'websocket._socket',
    'websocket._ssl_compat',
    'websocket._url',
    'websocket._utils',
    'jinja2',
    'markupsafe',
    'itsdangerous',
    'click',
    'api_server',
    'portal_client',
    'session_manager',
    'network_utils',
    'config',
    'result_types',
    'ai_audit_client',
    'captcha_ocr',
    'ddddocr',
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
    'numpy._globals',
    'protobuf',
    'google',
    'google.protobuf'
]

hiddenimports.extend(collect_submodules('urllib3'))
hiddenimports.extend(collect_submodules('flask'))
hiddenimports.extend(collect_submodules('werkzeug'))

datas = []
datas.extend(collect_data_files('PySide6', include_py_files=False, subdir='plugins/platforms'))
datas.extend(collect_data_files('PySide6', include_py_files=False, subdir='plugins/styles'))
datas.extend(copy_metadata('PySide6'))
datas.extend(copy_metadata('shiboken6'))

try:
    datas.extend(collect_data_files('ddddocr', include_py_files=False))
    datas.extend(copy_metadata('ddddocr'))
    print("Collected ddddocr data files")
except Exception as e:
    print(f"Warning: Could not collect ddddocr data files: {e}")

try:
    datas.extend(collect_data_files('onnxruntime', include_py_files=False))
    datas.extend(copy_metadata('onnxruntime'))
    hiddenimports.extend(collect_submodules('onnxruntime'))
    print("Collected onnxruntime data files and submodules")
except Exception as e:
    print(f"Warning: Could not collect onnxruntime data files: {e}")

try:
    import ddddocr
    ddddocr_path = os.path.dirname(ddddocr.__file__)
    for root, dirs, files in os.walk(ddddocr_path):
        for f in files:
            if f.endswith('.onnx') or f.endswith('.json'):
                src = os.path.join(root, f)
                rel_path = os.path.relpath(root, ddddocr_path)
                datas.append((src, os.path.join('ddddocr', rel_path)))
    print("Collected ddddocr model files")
except Exception as e:
    print(f"Warning: Could not collect ddddocr model files: {e}")

spec_dir = os.path.dirname(os.path.abspath(SPEC))
datas.append((os.path.join(spec_dir, 'service_config.json'), '.'))

binaries = []
try:
    import PySide6
    pyside6_path = os.path.dirname(PySide6.__file__)
    
    platforms_dir = os.path.join(pyside6_path, 'plugins', 'platforms')
    if os.path.exists(platforms_dir):
        for f in os.listdir(platforms_dir):
            if f.endswith('.dll'):
                binaries.append((os.path.join(platforms_dir, f), 'PySide6/plugins/platforms'))
    
    styles_dir = os.path.join(pyside6_path, 'plugins', 'styles')
    if os.path.exists(styles_dir):
        for f in os.listdir(styles_dir):
            if f.endswith('.dll'):
                binaries.append((os.path.join(styles_dir, f), 'PySide6/plugins/styles'))
    
    for item in os.listdir(pyside6_path):
        item_path = os.path.join(pyside6_path, item)
        if os.path.isfile(item_path):
            if item.endswith('.pyd'):
                binaries.append((item_path, 'PySide6'))
                        
except Exception as e:
    print(f"Warning: Could not collect PySide6 binaries: {e}")

try:
    import onnxruntime
    ort_path = os.path.dirname(onnxruntime.__file__)
    for root, dirs, files in os.walk(ort_path):
        for f in files:
            if f.endswith('.dll') or f.endswith('.pyd') or f.endswith('.so'):
                src = os.path.join(root, f)
                rel_path = os.path.relpath(root, ort_path)
                binaries.append((src, os.path.join('onnxruntime', rel_path)))
    print("Collected onnxruntime binaries")
except Exception as e:
    print(f"Warning: Could not collect onnxruntime binaries: {e}")

excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'cv2',
    'torch',
    'tensorflow',
    'IPython',
    'jupyter',
    'notebook',
    'PyQt6',
    'PyQt5',
    'PyQt4',
    'PySide2',
    'PySide',
    'pytest',
    'sphinx',
    'docutils',
    'curses',
    'tty',
    'pty',
    'fcntl',
    'pipes',
    'resource',
    'syslog',
    'venv',
    'ensurepip',
    'idlelib',
    'turtledemo',
    'test',
    'tests',
    'gdbm',
    'PySide6.Qt3D',
    'PySide6.QtBluetooth',
    'PySide6.QtCharts',
    'PySide6.QtDataVisualization',
    'PySide6.QtDesigner',
    'PySide6.QtHelp',
    'PySide6.QtHttpServer',
    'PySide6.QtLocation',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtNetworkAuth',
    'PySide6.QtNfc',
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',
    'PySide6.QtPdf',
    'PySide6.QtPdfWidgets',
    'PySide6.QtPositioning',
    'PySide6.QtQuick',
    'PySide6.QtQuick3D',
    'PySide6.QtQuickControls2',
    'PySide6.QtQuickWidgets',
    'PySide6.QtRemoteObjects',
    'PySide6.QtScxml',
    'PySide6.QtSensors',
    'PySide6.QtSerialBus',
    'PySide6.QtSerialPort',
    'PySide6.QtSpatialAudio',
    'PySide6.QtSql',
    'PySide6.QtStateMachine',
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
    'PySide6.QtTest',
    'PySide6.QtTextToSpeech',
    'PySide6.QtUiTools',
    'PySide6.QtWebChannel',
    'PySide6.QtWebEngine',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineQuick',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebSockets',
    'PySide6.QtWebView',
    'PySide6.QtXml'
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
