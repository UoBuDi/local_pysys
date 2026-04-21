# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata

block_cipher = None

hiddenimports = [
    'PySide6',
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
    '81d243bd2c585b0f4821__mypyc',
    'websockets',
    'jinja2',
    'markupsafe',
    'itsdangerous',
    'click',
    'blink',
    'api_server',
    'portal_client',
    'session_manager',
    'network_utils',
    'config',
    'result_types',
    'ai_audit_client'
]

hiddenimports.extend(collect_submodules('urllib3'))
hiddenimports.extend(collect_submodules('charset_normalizer'))
hiddenimports.extend(collect_submodules('flask'))
hiddenimports.extend(collect_submodules('werkzeug'))
hiddenimports.extend(collect_submodules('PySide6'))
hiddenimports.extend(collect_submodules('shiboken6'))
hiddenimports.extend(collect_submodules('websockets'))

try:
    import charset_normalizer
    charset_path = os.path.dirname(charset_normalizer.__file__)
    for root, dirs, files in os.walk(charset_path):
        for f in files:
            if f.endswith('.pyd') and '__mypyc' in f:
                module_name = f.replace('.pyd', '')
                hiddenimports.append(f'charset_normalizer.{module_name}')
except Exception as e:
    print(f"Warning: Could not collect charset_normalizer mypyc modules: {e}")

try:
    import charset_normalizer
    charset_path = os.path.dirname(charset_normalizer.__file__)
    for root, dirs, files in os.walk(charset_path):
        for f in files:
            if f.endswith('.pyd'):
                src = os.path.join(root, f)
                rel_path = os.path.relpath(root, charset_path)
                binaries.append((src, os.path.join('charset_normalizer', rel_path)))
except Exception as e:
    print(f"Warning: Could not collect charset_normalizer binaries: {e}")

try:
    mypyc_module = r'C:\Program Files\Python313\Lib\site-packages\81d243bd2c585b0f4821__mypyc.cp313-win_amd64.pyd'
    if os.path.exists(mypyc_module):
        binaries.append((mypyc_module, '.'))
        print(f"Added mypyc module: {mypyc_module}")
except Exception as e:
    print(f"Warning: Could not add mypyc module: {e}")

datas = []
datas.extend(collect_data_files('PySide6', include_py_files=False))
datas.extend(copy_metadata('PySide6'))
datas.extend(copy_metadata('shiboken6'))

spec_dir = os.path.dirname(os.path.abspath(SPEC))
datas.append((os.path.join(spec_dir, 'service_config.json'), '.'))

binaries = []
try:
    import PySide6
    pyside6_path = os.path.dirname(PySide6.__file__)
    
    for item in os.listdir(pyside6_path):
        item_path = os.path.join(pyside6_path, item)
        if os.path.isfile(item_path):
            if item.endswith('.dll') or item.endswith('.pyd'):
                binaries.append((item_path, 'PySide6'))
        elif os.path.isdir(item_path):
            for root, dirs, files in os.walk(item_path):
                for f in files:
                    if f.endswith('.dll'):
                        src = os.path.join(root, f)
                        rel_path = os.path.relpath(root, pyside6_path)
                        binaries.append((src, os.path.join('PySide6', rel_path)))
                        
except Exception as e:
    print(f"Warning: Could not collect PySide6 binaries: {e}")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
        'IPython',
        'jupyter',
        'notebook',
        'PyQt6',
        'PyQt5'
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
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
