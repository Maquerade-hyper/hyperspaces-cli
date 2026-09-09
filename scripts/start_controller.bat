@echo off
setlocal

cd /d "%~dp0.."

call .venv\Scripts\activate.bat

echo ========================================
echo       HYPERSPACE CONTROLLER
echo ========================================
echo.

python -m apps.control_plane.main

endlocal