@echo off
setlocal

cd /d "%~dp0.."

call .venv\Scripts\activate.bat

echo ========================================
echo           HYPERSPACE
echo ========================================
echo.
echo Starting runtime manager...
echo.

python scripts\runtime_manager.py

echo.
echo ========================================
echo Hyperspace runtime stopped.
echo ========================================
echo.

endlocal