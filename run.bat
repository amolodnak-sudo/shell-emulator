@echo off
cd /d "%~dp0"
py src/emulator.py --vfs-path ./vfs/vfs.xml --script ./tests/test_script.sh
echo.
pause