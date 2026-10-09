@echo off
cd /d "%~dp0"
python export_secrets.py
echo.
pause
