@echo off
setlocal

cd /d "%~dp0.."

echo ========================================
echo      RESTART HYPERSPACE
echo ========================================
echo.

call scripts\stop_hyperspace.bat

timeout /t 2 /nobreak >nul

echo.
echo Starting Hyperspace...
echo.

call scripts\start_hyperspace.bat

endlocal