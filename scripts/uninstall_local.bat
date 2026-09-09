@echo off
setlocal

cd /d "%~dp0.."

echo ========================================
echo      HYPERSPACE LOCAL UNINSTALL
echo ========================================
echo.

echo This operation removes the local installation
echo metadata only.
echo.
echo Runtime data, identities, meshes, jobs, artifacts,
echo certificates and logs will NOT be deleted.
echo.

choice /C YN /N /M "Remove installation metadata? [Y/N]: "

if errorlevel 2 (
    echo.
    echo Uninstall cancelled.
    exit /b 0
)

if exist "data\config\installation.json" (
    del /Q "data\config\installation.json"
    echo Installation metadata removed.
) else (
    echo No installation metadata found.
)

echo.
echo Runtime data preserved.
echo.

endlocal