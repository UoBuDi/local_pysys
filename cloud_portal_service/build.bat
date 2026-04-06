@echo off
chcp 65001 >nul 2>&1
cls

echo Installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install pyside6 --quiet
python -m pip install nuitka --quiet
python -m pip install zstandard --quiet
python -m pip install websocket-client --quiet

echo Updating version...
python update_version.py

echo Cleaning build directories...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo Building executable...
nuitka --onefile --windows-console-mode=disable --enable-plugin=pyside6 --output-dir=dist --output-filename=CloudPortalService.exe main.py

echo Copying configuration file...
copy /y service_config.json dist\service_config.json >nul

echo Build complete!
echo Output: dist\CloudPortalService.exe
echo Config: dist\service_config.json
pause
