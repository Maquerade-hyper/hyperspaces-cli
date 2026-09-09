@echo off
setlocal

cd /d "%~dp0.."

call .venv\Scripts\activate.bat

echo ========================================
echo          HYPERSPACE AGENT
echo ========================================
echo.

python -m apps.agent.main

endlocal